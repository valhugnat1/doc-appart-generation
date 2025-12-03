terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.30.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "scaleway" {
  zone   = var.zone
  region = var.region
}
