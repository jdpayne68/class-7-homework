# Test

curl "$(terraform output -raw api_url)/python?name=Chewbacca"
curl "$(terraform output -raw api_url)/node?name=Malgus"

Test WAF

curl "$(terraform output -raw api_url)/python?name=<script>alert(1)</script>"

🧠 Checkpoint

Students must explain:

    Why Lambda permission is required
    Difference between integration vs route
    Where WAF sits
    Why Terraform is better than ClickOps

“ClickOps proves it works. Terraform proves you can rebuild it.”

“If it’s not in code, it doesn’t exist.”

“Real engineers don’t click. They declare.”
