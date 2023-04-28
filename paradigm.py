import argparse
import yaml
import docker
import os
import shutil
import sys
import subprocess
import json
from halo import Halo


spinner = Halo(text='⚡ Processing...', spinner='dots12')

def convert_ipynb_to_py(input_file, step):
    output_file = f"./{step}/" + os.path.splitext(input_file)[0] + ".py"
    with open(input_file, "r", encoding="utf-8") as file:
        notebook = json.load(file)

    with open(output_file, "w", encoding="utf-8") as output:
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                code = "".join(cell["source"])
                output.write(code)
                output.write("\n\n")

def build_and_push_docker_image(step, repo_name):
    client = docker.from_env()
    image_tag = f"{repo_name}/{step}:latest"

    # Create step directory if not exists
    step_dir = f"./{step}"
    if not os.path.exists(step_dir):
        os.mkdir(step_dir)

    # Copy Python file and requirements.txt to step directory
    # also convert any notebook to a python script
    if os.path.exists(f"{step}.ipynb"):
        convert_ipynb_to_py(f"{step}.ipynb", step)
    else:
        shutil.copy(f"{step}.py", step_dir)

    # if no requirements for a file, create an empty requirements file
    if os.path.exists(f"requirements.{step}"):
        shutil.copy(f"requirements.{step}", step_dir)
    else:
        with open(f"{step_dir}/" + f"requirements.{step}", "w") as file:
            file.write("")

    # Rename requirements.txt in step directory
    os.rename(f"{step_dir}/requirements.{step}", f"{step_dir}/requirements.txt")

    # Generate Dockerfile
    dockerfile_content = f"""\
FROM python:3.9

WORKDIR /app

COPY ./{step}.py /app
COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./{step}.py"]
"""

    dockerfile_path = f"{step_dir}/Dockerfile"
    with open(dockerfile_path, "w") as dockerfile:
        dockerfile.write(dockerfile_content)

    print(f"Building Docker image: {image_tag}")
    image, _ = client.images.build(path=step_dir, tag=image_tag)
    # print("Pushing Docker image...")
    # client.images.push(repo_name, tag=f"{step}:latest")
    # client.images.push(f"{repo_name}/{step}", tag="latest", stream=True, decode=True)
    # print(f"Image {image_tag} pushed successfully")

def containerize_steps(repo_name, steps):
    for step in steps:
        if not os.path.exists(step):
            os.mkdir(step)
        build_and_push_docker_image(step, repo_name)

def create_workflow_yaml(repo_name, steps=None, dependencies=None, deployment_step=None, deployment_port=None, name=None):
    dag_tasks = []
    container_templates = []

    if steps:
        for step in steps:
            task_name = f"step-{step}"
            dag_task = {
                "name": task_name,
                "template": step
            }

            if step in dependencies:
                dag_task["dependencies"] = [f"step-{d}" for d in dependencies[step]]

            dag_tasks.append(dag_task)

            container_templates.append({
                "name": step,
                "container": {
                    "image": f"{repo_name}/{step}:latest",
                    "command": ["python", f"{step}.py"],
                    "imagePullPolicy": "IfNotPresent"
                }
            })

    templates = [
        {
            "name": "dag-steps",
            "dag": {
                "tasks": dag_tasks
            }
        },
        *container_templates
    ]

    if deployment_step:

        if deployment_step in dependencies:
            deploy_task = {
                "name": f"step-{deployment_step}",
                "dependencies": [f"step-{d}" for d in dependencies[deployment_step]],
                "template": f"deploy-{deployment_step}"
            }
        else:
            deploy_task = {
                "name": f"step-{deployment_step}",
                "template": f"deploy-{deployment_step}"
            }
        dag_tasks.append(deploy_task)

        deployment_template = {
            "name": f"deploy-{deployment_step}",
            "script": {
                "image": "bitnami/kubectl:latest",
                "command": ["/bin/bash"],
                "source": f"""kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: deploy-{deployment_step}
spec:
  type: NodePort
  selector:
    app: deploy-{deployment_step}
  ports:
    - protocol: TCP
      port: 80
      targetPort: {deployment_port}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-{deployment_step}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: deploy-{deployment_step}
  template:
    metadata:
      labels:
        app: deploy-{deployment_step}
    spec:
      containers:
      - name: {deployment_step}
        image: {repo_name}/{deployment_step}:latest
        ports:
        - containerPort: {deployment_port}
        imagePullPolicy: IfNotPresent
EOF"""
                
            },
        }



        templates.append(deployment_template)


    workflow = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {
            "generateName": f"{name}-"
        },
        "spec": {
            "entrypoint": "dag-steps",
            "serviceAccountName": "argo-workflow",
            "templates": templates
        }
    }

    return yaml.dump(workflow, sort_keys=False)



def launch(args):
    spinner.start()
    containerize_steps(args.repo, args.steps)
    spinner.stop()

def parse_dependencies(dependencies_str):
    dependencies = {}
    if dependencies_str:
        for dep_str in dependencies_str.split(','):
            key, value_str = dep_str.split(':')
            values = value_str.split('|')
            dependencies[key.strip()] = [v.strip() for v in values]
    return dependencies


def run_argo_submit(file_path):
    command = ['argo', 'submit', '-n', 'argo', '--watch', file_path]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Output:\n", result.stdout)
        print("Error (if any):\n", result.stderr)

    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        print("Output:\n", e.output)
        print("Error:\n", e.stderr)


def deploy(args):
    # dependencies = []
    # for dep in args.dependencies:
    #     if dep.lower() == "none":
    #         dependencies.append(None)
    #     else:
    #         dependencies.append(dep.split(","))

    dependencies = parse_dependencies(args.dependencies)

    yaml_file = create_workflow_yaml(args.repo, steps=args.steps, dependencies=dependencies, deployment_step=args.deployment, deployment_port=args.deployment_port, name=args.name)

    with open(args.output, "w") as f:
        f.write(yaml_file)

    print(f"Generated Argo Workflow YAML file: {args.output}")

    print("Sumitting Workflow to Cluster")
    print("Waiting for progress and logs")
    spinner.start()
    run_argo_submit(args.output)
    spinner.stop()

    print(f"Completed running the Workflow")

def main():
    parser = argparse.ArgumentParser(description="Paradigm: Fastest ML Pipelines")
    subparsers = parser.add_subparsers()

    # Launch subcommand
    parser_launch = subparsers.add_parser("launch", help="Containerize steps and push Docker images to the repository")
    parser_launch.add_argument("--repo", required=True, help="Container registry repository name")
    parser_launch.add_argument("--steps", required=True, nargs="+", help="List of step names")
    parser_launch.set_defaults(func=launch)

    # Deploy subcommand
    parser_deploy = subparsers.add_parser("deploy", help="Deploy the Pipelines")
    parser_deploy.add_argument("--repo", required=True, help="Container registry repository name")
    parser_deploy.add_argument("--steps", default=None, nargs="+", help="List of step names")
    parser_deploy.add_argument("--dependencies", default=None, help="Step dependencies in the format: stepA:dep1|dep2,stepB:dep1|dep2|dep3")
    parser_deploy.add_argument("--deployment", default=None, help="Deployment step name, leave blank for no deployment step")
    parser_deploy.add_argument("--deployment_port", default=None, help="The port number of the deployment app")
    parser_deploy.add_argument("--output", default="workflow.yaml", help="Output YAML file name")
    parser_deploy.add_argument("--name", default="paradigm-pipeline", help="Name of the pipeline")
    parser_deploy.set_defaults(func=deploy)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
