# Reliability

Primary reliability risks in this repository:

- generator output not matching expected JSON
- subtitle parsing edge cases
- frame extraction failures
- shell command quoting and workspace mutations

Mitigate by validating schemas, keeping prompts explicit, and testing against small local fixtures.
