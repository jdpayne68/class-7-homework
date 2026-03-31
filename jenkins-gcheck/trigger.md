# Add GitHub Webhook Trigger to Jenkins

## Prerequisites
- Jenkins running on EC2
- Jenkins reachable from the internet (e.g. `http://<EC2-PUBLIC-IP>:8080`)
- Repo with Jenkinsfile and terraform script 
- Github and git plugins

---


## Jenkins Config

### Make a pipeline 

1. Jenkins dashboard → New Item
2. Name it
3. Select: Pipeline
4. Click OK

### Enable GitHub Trigger 

In job configuration:

- Triggers → GitHub hook trigger for GITScm polling

### Configure

- Definition: Pipeline script from SCM
- SCM: Git
- Add HTTP repo URL
- Branch:
  `*/main`
- Script Path:
  Jenkinsfile




Save pipeline

---

## Add GitHub Webhook 
Go to Github

Repository → Settings → Webhooks → Add webhook

- Payload URL:
  `http://<YOUR-JENKINS-URL>/github-webhook/`

- Content type:
  `application/json`

- Events:
  Just the push event

Save

---

## Test

Option A:
```bash
git commit --allow-empty -m "test webhook"
git push origin main
```

Option B:
- GitHub → Webhook → Recent Deliveries
- Redeliver

---





## Troubleshooting

### Expected Result
- Push event occurs on repo
- Webhook sent from GitHub
- Jenkins job starts automatically

### Common issues
Jenkins not reachable:
- Ensure public IP or DNS
- Open port 8080 in security group

Incorrect webhook URL:
- Must end with `/github-webhook/`

No build triggered:
- Verify trigger enabled in Jenkins
- Check webhook delivery status (200 OK)

## What Is Happing and How It Works

### What a Webhook Is

A webhook is an HTTP callback.

- One system sends an HTTP request to another system when an event happens
- No polling is required
- It is event-driven

In this case:
- GitHub = sender
- Jenkins = receiver

---

### What Happens Step by Step

1. You push code to GitHub
2. GitHub detects a `push` event
3. GitHub sends an HTTP POST request to:
   `http://<jenkins-url>/github-webhook/`
4. Jenkins receives the request
5. Jenkins matches the event to a configured job
6. Jenkins triggers the pipeline
7. Jenkins reads the `Jenkinsfile` from the repo
8. Pipeline runs

---

### What the Webhook Sends

GitHub sends a JSON payload that includes:

- Repository name
- Branch
- Commit ID
- Commit message
- Author

Example (simplified):

```json
{
  "ref": "refs/heads/main",
  "repository": {
    "full_name": "aaron-dm-mcdonald/new-jenkins-s3-test"
  },
  "head_commit": {
    "id": "abc123",
    "message": "update"
  }
}