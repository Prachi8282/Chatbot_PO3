# Incident Playbook: Database Connection Failures

## 1. Incident Description and Symptoms
This runbook covers issues where the application backend loses connectivity to the primary banking database (PostgreSQL/Oracle). Common symptoms include:
- `ConnectionTimeoutException` or `OperationalError: could not connect to server` logs in the backend.
- API endpoints returning HTTP `500 Internal Server Error` with database errors.
- Database connection pool utilization hitting 100% capacity.
- Slow query warnings appearing in dashboard logs.

## 2. Diagnostics and Initial Checks
When a database incident is reported, the responding engineer must perform the following steps immediately:
1. **Network Connectivity Check**: Verify whether the database server is pingable from the application host. Run `ping db-primary.internal.bank` or `nc -zv db-primary.internal.bank 5432`.
2. **Resource Utilization Check**: Log into the database console and check CPU, RAM, and Disk space. If disk space is at 100%, the database will refuse new write operations.
3. **Active Connections Check**: Run the SQL query `SELECT count(*), state FROM pg_stat_activity GROUP BY state;` to determine if database connections are locked in idle transactions.

## 3. Mitigation and Recovery Procedures
Depending on the root cause discovered during diagnostics, perform the following actions:
- **Connection Pool Exhaustion**: If the pool is exhausted due to slow queries, increase the pool limit in the application configuration (e.g., set `DB_POOL_MAX=100` in `.env`) and restart the backend.
- **Database Service Restart**: If the database server is unresponsive, trigger a service restart:
  - PostgreSQL: `sudo systemctl restart postgresql`
  - Oracle: `sqlplus / as sysdba` followed by `SHUTDOWN IMMEDIATE;` and `STARTUP;`
- **Failover to Replica**: If the primary database hardware has failed, initiate automatic or manual database failover to the read-replica/hot standby. Run the failover script `/usr/local/bin/db-failover.sh` to promote the standby to primary.

## 4. Post-Incident Review and Prevention
Every database connection incident requires a post-mortem review. Preventative measures include configuring Prometheus alerts for connection pool thresholds above 80%, optimizing long-running SQL queries with appropriate indexes, and implementing connection-retry logic in the application ORM.
