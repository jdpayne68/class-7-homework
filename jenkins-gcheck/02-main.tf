resource "aws_s3_bucket" "frontend" {
  bucket_prefix  = "class7-gcheck"
  force_destroy  = true

  tags = {
    Name = "class7-gcheck-bucket"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "public_read_access" {
  bucket     = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.frontend.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_s3_object" "screenshots" {
  for_each     = fileset("${path.module}/screenshots", "*.png")
  bucket       = aws_s3_bucket.frontend.id
  key          = each.value
  source       = "${path.module}/screenshots/${each.value}"
  content_type = "image/png"
}
