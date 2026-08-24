# Incident Playbook: Distributed Denial of Service (DDoS) Mitigation

## 1. Incident Description and Indicators
A Distributed Denial of Service (DDoS) incident occurs when malicious actors flood the bank's public-facing APIs or web portals with excessive traffic, causing system slowdowns or total outages for legitimate users. Indicators of an active DDoS attack include:
- Bandwidth utilization spiking to 10x normal levels.
- Cloudflare dashboard showing a surge in HTTP 502/503 errors and blocked requests.
- Internal gateway CPU usage pegged at 100%.
- A sudden increase in traffic from a specific country or set of IP ranges without business rationale.

## 2. Detection and Identification
Identify the type of DDoS attack to apply the correct countermeasure:
1. **Volumetric Attacks (Layer 3/4)**: High bandwidth flooding (UDP/TCP SYN flood). Checked via netstat/conntrack tools.
2. **Application Layer Attacks (Layer 7)**: HTTP floods aiming to exhaust server resources (e.g. hitting slow, resource-heavy search endpoints). Checked via web access logs using query patterns.
3. **SSL/TLS Exhaustion**: Exploiting the handshake process to consume CPU.

## 3. Mitigation Steps
Initiate the following security countermeasures:
- **Enable Cloudflare "Under Attack" Mode**: Log into the Cloudflare console, navigate to the affected zone, and toggle "Under Attack" mode to force JavaScript challenges for all incoming web requests.
- **Implement Rate Limiting**: Adjust the API Gateway rate limit rules. Reduce the threshold to 60 requests per minute per IP for retail APIs.
- **Block Malicious IP Ranges**: Use the iptables commands or Cloudflare firewall rules to block the originating IPs. For example: `iptables -A INPUT -s <IP_RANGE> -j DROP`.
- **Geoblocking**: Temporarily restrict access from non-operational countries if the attack is highly localized geographically.

## 4. Post-Attack Recovery and Reporting
Once traffic returns to baseline levels, disable the restrictive "Under Attack" mode to restore the normal user experience. Compile a post-incident report listing: total requests blocked, estimated attack size (Gbps/RPS), list of target endpoints, and recommendations for permanent rate-limiting policies on vulnerable endpoints.
