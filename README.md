# Paradigm ⚡

[![version](https://img.shields.io/badge/version-0.1-yellow)]() [![discord](https://img.shields.io/badge/chat-discord-blueviolet)]()

Paradigm Lightning is a light-weight, blazing-fast tool to package your ML code into pipelines and deploy on Kubernetes. No need to refactor any code for production. Paradigm Lightning can read your Python notebooks and scripts and prepare them quickly for scalable production. 


# Quickstart

## To Deploy in AWS ☁️

You need a Kubernetes cluster and `kubectl` set up to be able to access that cluster. On AWS, we use Amazon Elastic Kubernetes Service (Amazon EKS) for this. 
- Please refer to the [Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html) on how to set things up
- Make sure you can [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) installed and configured as well

Also, make sure [Docker](https://docs.docker.com/engine/install/) is installed and running in your environment

### Set up Paradigm

In a terminal with the above kubectl access, follow the below steps.

- (Recommended) Create a new Python environment with your preferred environment manager
- Clone this repo 
    - `git clone https://github.com/ParadigmAI/paradigm.git`
- Go into the directory 
    - `cd paradigm`
- Rename setup-aws.py as setup.py
    - `mv setup-aws.py setup.py`
- Make the installation script executable 
    - `chmod +x install-aws.sh`
- Run the intallation script 
    - `./install-aws.sh`
- Validate if paradigm was properly installed
    - `paradigm --help`
- Finally apply permissions for service account
    - `kubectl apply -f rbac.yaml` 

### Now let's move into your ML project folder

Your folder can contain one or more scripts/notebooks that you want to execute as steps in an ML pipeline.

- The preferred directory structure should be as follows. In the below example, `p1, p2 and p3` represent any python script or notebook you have. (Refer the [examples/basic](./examples/basic))
    - IMPORTANT - note the `requirements.<file name>` files. You have to create a txt with the specific naming convention **only for the scripts or notebooks that need have additional dependencies**. It should include all the dependecies that are required for each step. (Refer the [examples/basic](./examples/basic)). We promise this is the only file addition before taking your ML code to prodution.
```
    - 📁 project_root
        - 📄 p1.py
        - 📄 p2.ipynb
        - 📄 p3.py
        - 📄 requirements.p1
        - 📄 requirements.p3
```

- Now we are ready to let Paradigm get the code ready before deploying to the Kubernetes cluster. Include the scripts/notebook you want as steps in the below command. Choose any name as `<repo_name>` for the pipeline steps.
```
paradigm launch --repo <repo_name> --steps p1 p2 p3 --region_name us-east-1
```
- To the final step. Deploy the pipeline with the below command.
    - `<repo_name>` should be the same as above
    - `--dependencies "p2:p1,p3:p2|p1"` defines the graph stucture on how the steps should be run. In this example, we are infomring that step `p2` is dependent on `p1` and step `p3` is actually depending on both `p2` and `p1`. 
    - In our example, `p3` is a service that needs to be run at the end of the pipeline. Sort of like an endpoint. Hence, we don't mention is under `--steps`, but rather under `--deployment`. If it the service is shuold be exposed via a port, that should be mentioned uner `--deployment_port`. 
    - `<pipeline_name>` is just any name that you want to give this particualr pipeline. Can be the same as `<repo_name>` too.
```
paradigm deploy --repo <repo_name>  --steps p1 p2 --dependencies "p2:p1,p3:p2|p1" --deployment p3 --deployment_port <if deplyment step has a post exposed> --output workflow.yaml --name <pipeline_name>
```

## To Deploy Locally 💻

You need a Kubernetes cluster and `kubectl` set up to be able to access that cluster. For this to run locally, we recommend using `minikube`.
- Please refer to the [minikube documentation](https://minikube.sigs.k8s.io/docs/)

### Set up Paradigm

- (Recommended) Create a new Python environment with your preferred environment manager
- Clone this repo 
    - `git clone https://github.com/ParadigmAI/paradigm.git`
- Go into the directory 
    - `cd paradigm`
- Rename setup-local.py as setup.py, Use the below commands
    - `mv setup-local.py setup.py`
- Make the installation script executable 
    - `chmod +x install.sh`
- Run the intallation script 
    - `./install.sh`
- Validate if paradigm was properly installed
    - `paradigm --help`
- Finally apply permissions for service account
    - `kubectl apply -f rbac.yaml` 

### Now let's move into your ML project folder

Your folder can contain one or more scripts/notebooks that you want to execute as steps in an ML pipeline.

- First, let's configure your current terminal session to use the Docker daemon inside the Minikube environment instead of the default Docker daemon on your host machine. This eliminated teh need for an image registry when working locally.
    - `eval $(minikube docker-env)`

- The preferred directory structure should be as follows. In the below example, `p1, p2 and p3` represent any python script or notebook you have. (Refer the [examples/basic](./examples/basic))
    - IMPORTANT - note the `requirements.<file name>` files. You have to create a txt with the specific naming convention **only for the scripts or notebooks that need have additional dependencies**. It should include all the dependecies that are required for each step. (Refer the [examples/basic](./examples/basic)). We promise this is the only file addition before taking your ML code to prodution.
```
    - 📁 project_root
        - 📄 p1.py
        - 📄 p2.ipynb
        - 📄 p3.py
        - 📄 requirements.p1
        - 📄 requirements.p3
```

- Now we are ready to let Paradigm get the code ready before deploying to the Kubernetes cluster. Include the scripts/notebook you want as steps in the below command. Choose any name as `<repo_name>` for the pipeline steps.
```
paradigm launch --repo <repo_name> --steps p1 p2 p3
```
- To the final step. Deploy the pipeline with the below command.
    - `<repo_name>` should be the same as above
    - `--dependencies "p2:p1,p3:p2|p1"` defines the graph stucture on how the steps should be run. In this example, we are infomring that step `p2` is dependent on `p1` and step `p3` is actually depending on both `p2` and `p1`. 
    - In our example, `p3` is a service that needs to be run at the end of the pipeline. Sort of like an endpoint. Hence, we don't mention is under `--steps`, but rather under `--deployment`. If it the service is shuold be exposed via a port, that should be mentioned uner `--deployment_port`. 
    - `<pipeline_name>` is just any name that you want to give this particualr pipeline. Can be the same as `<repo_name>` too.
```
paradigm deploy --repo <repo_name>  --steps p1 p2 --dependencies "p2:p1,p3:p2|p1" --deployment p3 --deployment_port <if deplyment step has a post exposed> --output workflow.yaml --name <pipeline_name>
```
- (OPTIONAL) If you want to access the service that is deployed in the previous set (for example an API endpoint), the following code has to be run since we're working inside minikube. 

    - `minikube service deploy-p3 -n argo`

- (OPTIONAL) In case you want to delete the running service, use the following commands
    - kubectl delete service deploy-p3 -n argo
    - kubectl delete deployment deploy-p3 -n argo


<br/><br/>


## Contributing

Suggestions on additional features and functionality are highly appreciated. General instructions on how to contribute are mentioned in [CONTRIBUTING](CONTRIBUTING.md)

## Getting help

Please use the issues tracker of this repository to report on any bugs or questions you have.

Also you can join the [DISCORD]()