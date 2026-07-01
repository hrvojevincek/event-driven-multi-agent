output "state_machine_arn" {
  description = "Research fan-out Step Functions state machine ARN."
  value       = aws_sfn_state_machine.research_fanout.arn
}

output "state_machine_name" {
  description = "Research fan-out Step Functions state machine name."
  value       = aws_sfn_state_machine.research_fanout.name
}
