# Remaining external gates · 0.5.1

1. Calendar setup and prior consent/selected target are recorded. The old two-hour session now returns AUTH_REQUIRED. Fresh owner consent is now complete (connected=true), but Google returned404 for the supplied old ID. Owner screenshot now confirms successful existing-calendar recovery; target selection and event operations are the next gates. No repeat login or Console setup. Exact one-event owner approval/write/read-back/retry without duplicates/undo/revocation remain unverified.
2. Historical 0.5.0 native Open/Cancel/import/refresh and original 45/95 are verified. New 0.5.1 packages do not imply installation. Native Passport Save/import/reopen and real notification/banner/click-focus need owner interaction. Windows automation stopped through Escape remains stopped.
3. Original managed GCP criterion is unmet. Organizers will provide no GCP. Prepared Agent Engine/IAM/shared-state scripts remain disabled and do not block Render/Gemini/MCP. No official alternative-architecture waiver, personal billing, paid trial activation or resources are assumed.

NON_GCP_READY=false while gates 1–2 remain. See docs/remaining_actions_0.5.1.md. Free quotas and temporary hosting remain operational limits.

Installer correction: the first 0.5.1 NSIS package incorrectly installed on C: while D: retained 0.5.0. The replacement compiled successfully with a fixed D: destination and no LocalAppData installer cache; three structural regression guards passed. Owner installation on D: and physical acceptance remain pending; the agent has not resumed Windows control. See docs/evidence/final-0.5.1-windows-D-install-fix.json.
