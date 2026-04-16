# Mobile Health Support Manual

## Domain Assumptions

- This domain models a United States outpatient remote patient monitoring program for home blood pressure support.
- The patient is an established participant in a connected blood pressure monitoring workflow.
- The assistant supports technology recovery and care coordination only.

## Supported Troubleshooting Scope

- Identity verification
- Monitoring enrollment and consent status review
- Device assignment review
- Consent renewal support
- Pairing recovery after a phone change
- App permission repair
- Fresh verification reading and upload confirmation

## Out of Scope

- Diagnosis
- Medication changes
- Treatment recommendations
- Interpretation of blood pressure values beyond narrow safety interrupts

## Safety and Privacy Rules

- Verify identity before disclosing monitoring status, device assignment, or upload history.
- Share only minimum necessary information.
- Do not count a manually typed blood pressure value as a successful RPM upload.
- If the user reports emergency red-flag symptoms, stop normal troubleshooting and escalate immediately.

## First-Task Workflow

1. Verify identity.
2. Check monitoring status and device assignment.
3. If consent is expired, resend consent and confirm the patient accepts it.
4. If pairing is broken after a phone change, issue a new pairing code and have the patient pair the cuff.
5. If Bluetooth permission is denied, have the patient grant the permission.
6. Ask for one fresh device reading.
7. Confirm the reading becomes provider-visible.

## Initial Task Set

- One baseline phone-upgrade recovery task
- Three single-failure variants
- Three mixed-failure variants
- Three persona overlays (`None`, `Easy`, `Hard`)
