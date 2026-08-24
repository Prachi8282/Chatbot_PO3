# Bank Security and Authentication Policy

## 1. Access Control and Multi-Factor Authentication (MFA)
All employee accounts accessing the banking core systems must be protected by mandatory Multi-Factor Authentication (MFA). MFA must utilize hardware security keys (FIDO2) or registered authentication apps (Google Authenticator or Duo). SMS-based 2FA is strictly prohibited for administrative access due to SIM-swapping risks. Password policies require a minimum of 16 characters containing upper/lower case letters, digits, and special characters. Passwords must be rotated every 90 days.

## 2. Remote access and VPN usage
Employees accessing internal banking resources from remote locations must connect via the corporate GlobalProtect VPN. VPN access is limited to authorized company-issued laptops running the latest security agent. Direct access to databases, transaction ledger systems, or internal APIs from outside the secure subnet is blocked. Any remote login attempt from an unregistered device or an unapproved country will trigger an automatic account suspension and notify the security operations team.

## 3. Suspicious Activity Reporting (SAR)
Any employee who detects suspicious transactions, unusual login attempts, or signs of social engineering must file a Suspicious Activity Report (SAR) within 2 hours of detection. SARs are submitted through the internal Sentinel Portal. Critical indicators of suspicious activity include: repeated password failures from a single IP, rapid consecutive logins from geographically distant locations (impossible travel), or attempts to modify transaction logs.

## 4. Workstation and Device Security Policies
All company-issued workstations must have full disk encryption (BitLocker for Windows, FileVault for macOS) enabled. USB storage devices are disabled by group policy. Automated screensavers must lock the screen after 5 minutes of inactivity. Leaving a logged-in workstation unattended in a public area is a Category 1 security violation and subject to disciplinary action.
