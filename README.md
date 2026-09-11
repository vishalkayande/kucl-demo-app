# Kucl Demo App

A simple Flask application demonstrating a complete **Docker + Docker Hub + Kubernetes deployment + rolling update** workflow.

This project is intended as a hands-on demo for:

* Building a Docker image
* Tagging and pushing images to Docker Hub
* Deploying an application to Kubernetes
* Exposing the application using a Kubernetes `NodePort` Service
* Running multiple replicas
* Performing a Kubernetes rolling update from `v1` to `v2`
* Verifying the deployment and rollout

---

## Architecture

```text
                 Docker Hub
                     |
             +-------+-------+
             |               |
        kucl-demo-app:v1  kucl-demo-app:v2
             |               |
             +-------+-------+
                     |
                 Kubernetes
                     |
              +------+------+
              | Deployment |
              |  replicas:3|
              +------+------+
                     |
          +----------+----------+
          |          |          |
       Pod v1     Pod v1     Pod v1
          |          |          |
          +----------+----------+
                     |
             demo-app-svc
                NodePort
                     |
                  Client
```

---

## Project Structure

```text
kucl-demo-app/
│
├── project1/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── deployment.yaml
│
└── README.md
```

---

# 1. Application

The application is a simple Flask web server.

## `project1/app.py`

```python
from flask import Flask
import socket
import os

app = Flask(__name__)


@app.route("/")
def home():
    return f"Hello from {socket.gethostname()} | Version: {os.getenv('APP_VERSION', 'v1')}"


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

The application provides two endpoints:

| Endpoint  | Description                                   |
| --------- | --------------------------------------------- |
| `/`       | Displays the hostname and application version |
| `/health` | Health-check endpoint                         |

Example response:

```text
Hello from demo-app-7f8c9d6f8b-x2abc | Version: v1
```

The hostname is useful for demonstrating that requests can be served by different Kubernetes Pods.

---

# 2. Python Dependencies

## `project1/requirements.txt`

```text
flask==3.0.0
```

---

# 3. Dockerfile

## `project1/Dockerfile`

Use the following Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}

EXPOSE 5000

CMD ["python", "app.py"]
```

### Why `ARG` is required

The Docker build commands use:

```bash
--build-arg APP_VERSION=v2
```

Therefore, the Dockerfile must declare:

```dockerfile
ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}
```

This allows the version to be changed during the image build.

---

# 4. Prerequisites

Make sure the following tools are installed:

* Docker
* Docker Hub account
* Kubernetes
* `kubectl`
* Minikube (if running Kubernetes locally)

Verify the installations:

```bash
docker --version
kubectl version --client
minikube version
```

---

# 5. Build Docker Image

Navigate to the application directory:

```bash
cd project1
```

Build version 1:

```bash
docker build -t <dockerhub-username>/kucl-demo-app:v1 .
```

Verify the image:

```bash
docker images
```

You should see something similar to:

```text
REPOSITORY                         TAG
<dockerhub-username>/kucl-demo-app v1
```

---

# 6. Login to Docker Hub

Login to Docker Hub:

```bash
docker login
```

Enter your Docker Hub username and password/token when prompted.

---

# 7. Push Version 1 to Docker Hub

Push the image:

```bash
docker push <dockerhub-username>/kucl-demo-app:v1
```

Replace:

```text
<dockerhub-username>
```

with your actual Docker Hub username.

For example:

```bash
docker push myusername/kucl-demo-app:v1
```

---

# 8. Build Version 2

Version 2 is used to demonstrate a Kubernetes rolling update.

Build the image:

```bash
docker build \
  -t <dockerhub-username>/kucl-demo-app:v2 \
  --build-arg APP_VERSION=v2 .
```

Verify:

```bash
docker images
```

You should now have both:

```text
<dockerhub-username>/kucl-demo-app:v1
<dockerhub-username>/kucl-demo-app:v2
```

---

# 9. Push Version 2 to Docker Hub

```bash
docker push <dockerhub-username>/kucl-demo-app:v2
```

At this point, Docker Hub should contain:

```text
kucl-demo-app:v1
kucl-demo-app:v2
```

---

# 10. Start Kubernetes

If you are using Minikube:

```bash
minikube start
```

Verify the cluster:

```bash
kubectl cluster-info
```

Check the nodes:

```bash
kubectl get nodes
```

Example:

```text
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.xx.x
```

---

# 11. Kubernetes Deployment

Create a file named:

```text
deployment.yaml
```

Use the following configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
  labels:
    app: demo-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
    spec:
      containers:
        - name: demo-app
          image: <dockerhub-username>/kucl-demo-app:v1
          ports:
            - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: demo-app-svc
spec:
  selector:
    app: demo-app
  ports:
    - port: 80
      targetPort: 5000
  type: NodePort
```

### Important

Replace:

```text
<dockerhub-username>
```

with your actual Docker Hub username.

For example:

```yaml
image: myusername/kucl-demo-app:v1
```

---

# 12. Deploy the Application

Apply the Kubernetes manifest:

```bash
kubectl apply -f deployment.yaml
```

Expected output:

```text
deployment.apps/demo-app created
service/demo-app-svc created
```

---

# 13. Verify the Deployment

Check the Deployment:

```bash
kubectl get deployment
```

Example:

```text
NAME       READY   UP-TO-DATE   AVAILABLE
demo-app   3/3     3            3
```

Check the Pods:

```bash
kubectl get pods
```

Example:

```text
NAME                        READY   STATUS    RESTARTS   AGE
demo-app-7f8c9d6f8b-abc12   1/1     Running   0          30s
demo-app-7f8c9d6f8b-def34   1/1     Running   0          30s
demo-app-7f8c9d6f8b-ghi56   1/1     Running   0          30s
```

You can also view the Pods with node information:

```bash
kubectl get pods -o wide
```

---

# 14. Verify the Container Image

To check which image a Pod is using:

```bash
kubectl describe pod <pod-name> | grep "Image:"
```

Example:

```text
Image:  myusername/kucl-demo-app:v1
```

This confirms that Kubernetes is using the Docker image pushed to Docker Hub.

You can also use:

```bash
kubectl get pods -o jsonpath="{range .items[*]}{.metadata.name}{': '}{.spec.containers[0].image}{'\n'}{end}"
```

---

# 15. Verify the Service

Check the Kubernetes Service:

```bash
kubectl get svc demo-app-svc
```

Example:

```text
NAME             TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)
demo-app-svc     NodePort   10.96.123.45   <none>        80:30xxx/TCP
```

The application is exposed internally on port `80` and forwarded to the Flask container on port `5000`.

---

# 16. Access the Application with Minikube

The easiest way to access the NodePort Service is:

```bash
minikube service demo-app-svc --url
```

Example:

```text
http://192.168.49.2:30xxx
```

Open the URL in a browser or use `curl`:

```bash
curl $(minikube service demo-app-svc --url)
```

Example response:

```text
Hello from demo-app-7f8c9d6f8b-abc12 | Version: v1
```

---

# 17. Test the Health Endpoint

The application has a health endpoint:

```text
/health
```

Test it:

```bash
curl $(minikube service demo-app-svc --url)/health
```

Expected response:

```text
OK
```

---

# 18. Verify Load Balancing Across Pods

Because the Deployment has:

```yaml
replicas: 3
```

Kubernetes creates three Pods.

The application displays the Pod hostname:

```text
Hello from <pod-hostname> | Version: v1
```

Run multiple requests:

```bash
for i in {1..10}; do
  curl -s $(minikube service demo-app-svc --url)
  echo
done
```

Depending on the Kubernetes networking behavior, requests can be distributed across different Pods.

You can also watch the Pods:

```bash
kubectl get pods -w
```

---

# 19. Rolling Update: v1 → v2

Now update the application from version `v1` to `v2`.

Run:

```bash
kubectl set image deployment/demo-app \
  demo-app=<dockerhub-username>/kucl-demo-app:v2
```

For example:

```bash
kubectl set image deployment/demo-app \
  demo-app=myusername/kucl-demo-app:v2
```

Kubernetes will perform a rolling update.

Instead of stopping all Pods at once, Kubernetes gradually replaces the old Pods with new Pods.

---

# 20. Monitor the Rolling Update

Run:

```bash
kubectl rollout status deployment/demo-app
```

Expected output:

```text
Waiting for deployment "demo-app" rollout to finish...
Waiting for deployment "demo-app" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "demo-app" rollout to finish: 2 old replicas are pending termination...
deployment "demo-app" successfully rolled out
```

Check the Pods:

```bash
kubectl get pods
```

The newly created Pods should now be running version `v2`.

---

# 21. Verify Version 2

Check the image being used:

```bash
kubectl describe pod <pod-name> | grep "Image:"
```

Expected:

```text
Image: myusername/kucl-demo-app:v2
```

Access the application again:

```bash
curl $(minikube service demo-app-svc --url)
```

Expected response:

```text
Hello from demo-app-xxxxxxxxxx | Version: v2
```

---

# 22. Check Rollout History

Kubernetes stores rollout history for the Deployment.

Run:

```bash
kubectl rollout history deployment/demo-app
```

Example:

```text
deployment.apps/demo-app
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
```

You can inspect a particular revision:

```bash
kubectl rollout history deployment/demo-app --revision=2
```

---

# 23. Roll Back the Deployment

If version `v2` has a problem, Kubernetes can roll back to the previous version.

Run:

```bash
kubectl rollout undo deployment/demo-app
```

Monitor the rollback:

```bash
kubectl rollout status deployment/demo-app
```

Verify:

```bash
kubectl get pods
```

The Pods should return to the previous image/version.

---

# 24. Useful Kubernetes Commands

### List all resources

```bash
kubectl get all
```

### List Pods

```bash
kubectl get pods
```

### Detailed Pod information

```bash
kubectl describe pod <pod-name>
```

### View Pod logs

```bash
kubectl logs <pod-name>
```

### Follow Pod logs

```bash
kubectl logs -f <pod-name>
```

### List Deployments

```bash
kubectl get deployments
```

### List Services

```bash
kubectl get services
```

### View Deployment details

```bash
kubectl describe deployment demo-app
```

### View rollout status

```bash
kubectl rollout status deployment/demo-app
```

### View rollout history

```bash
kubectl rollout history deployment/demo-app
```

---

# 25. Clean Up

To remove the Kubernetes resources:

```bash
kubectl delete -f deployment.yaml
```

Verify:

```bash
kubectl get all
```

If you are finished with Minikube:

```bash
minikube stop
```

To completely delete the Minikube cluster:

```bash
minikube delete
```

---

# 26. End-to-End Workflow

The complete workflow can be summarized as:

```text
1. Write Flask application
          |
          v
2. Create Dockerfile
          |
          v
3. Build Docker image
          |
          v
4. Login to Docker Hub
          |
          v
5. Push v1 image
          |
          v
6. Start Kubernetes / Minikube
          |
          v
7. Deploy Kubernetes Deployment + Service
          |
          v
8. Verify 3 running Pods
          |
          v
9. Access application
          |
          v
10. Build and push v2
          |
          v
11. kubectl set image
          |
          v
12. Kubernetes rolling update
          |
          v
13. Verify v2
          |
          v
14. Roll back if required
```

---

# 27. Expected Final State

After deploying version `v1`, the Kubernetes environment should look approximately like:

```text
Deployment
└── demo-app
    ├── Pod 1 → kucl-demo-app:v1
    ├── Pod 2 → kucl-demo-app:v1
    └── Pod 3 → kucl-demo-app:v1

Service
└── demo-app-svc
    └── NodePort → Pods
```

After the rolling update:

```text
Deployment
└── demo-app
    ├── Pod 1 → kucl-demo-app:v2
    ├── Pod 2 → kucl-demo-app:v2
    └── Pod 3 → kucl-demo-app:v2

Service
└── demo-app-svc
    └── NodePort → Pods
```

---

# 28. Technologies Used

* **Python**
* **Flask**
* **Docker**
* **Docker Hub**
* **Kubernetes**
* **kubectl**
* **Minikube**

---

# 29. Learning Objectives

By completing this demo, you will understand:

* How to containerize a Flask application
* How Docker image tags such as `v1` and `v2` work
* How to push images to Docker Hub
* How Kubernetes Deployments manage application replicas
* How Kubernetes Services expose applications
* How `NodePort` works in a local Kubernetes environment
* How Kubernetes performs rolling updates
* How to monitor a rollout
* How to inspect rollout history
* How to roll back a Deployment

---

## License

This project is intended for learning and demonstration purposes.
