variable "table_name" { type = string }

variable "hash_key" { type = string }

variable "range_key" {
  type    = string
  default = null
}

variable "stream_enabled" {
  type    = bool
  default = false
}

variable "common_tags" { type = map(string) }

variable "attributes" {
  type = list(object({
    name = string
    type = string
  }))
}
