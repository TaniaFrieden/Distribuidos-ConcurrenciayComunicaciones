Deploy healthy mock server:

```bash
docker compose -f docker-compose-mock.yaml --profile healthy up
```

Deploy unhealthy mock server:

```bash
docker compose -f docker-compose-mock.yaml --profile unhealthy up
```
