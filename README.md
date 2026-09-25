# pyMbox - M-Box Monitor & Support 

A Python web app to log in to the M-Box SFTP* server and send its contents by mail.

It consumes Gmail's public SMTP* server to send e-mail.

The code is pushed from a GitHub* repository into the application platform.

The build is deployed on OpenShift* to run automatically every 6 hours.

## Scheduling

The script is orchestrated as a **Prefect flow** (`mbox_monitor_flow` in
`app.py`). The flow runs once per invocation; the 6-hour cadence is applied
through a Prefect deployment schedule instead of an in-process `time.sleep`.

Create a deployment that runs every 6 hours:

```bash
prefect deploy app.py:mbox_monitor_flow --interval 21600 --name mbox-monitor-every-6h
```

Then start a worker to execute the scheduled runs:

```bash
prefect worker start --pool default-agent-pool
```

### Glossary
__SFTP__ - Secure File Transfer Protocol

__SMTP__ - Simple Mail Transfer Protocol

__GitHub__ - Source code version control platform

__OpenShift__ - Red Hat's container platform

## Disclaimer
This is a live demo running on free plans and plenty can go wrong. Please understand that the developer might get nervous but if he made any mistake, typo or the such feel free to yell at him so he can correct them.

Enjoy your automatic e-mails!
