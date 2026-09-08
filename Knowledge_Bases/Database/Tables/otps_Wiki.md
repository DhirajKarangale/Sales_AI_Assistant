# Table: otps

## Table Description
The `otps` table stores information about one-time passwords (OTPs) that are sent to users' email addresses. Each record represents a unique OTP creation event.

## Columns

### id
- **Data Type:** integer
- **Description:** The unique identifier for each OTP record.
- **Business Use:** Used to uniquely identify each OTP event.
- **How the Column Affects the Record:** This is the primary key, ensuring each record is unique.
- **Example Values:**
  - 1
  - 2
  - 3
  - 4
  - 5

### created_at
- **Data Type:** timestamp without time zone
- **Description:** The timestamp indicating when the OTP was created.
- **Business Use:** Tracks the exact time when an OTP was generated.
- **How the Column Affects the Record:** Helps in tracking the validity and timeliness of OTPs.
- **Example Values:**
  - 2025-09-27 19:55:03.111000
  - 2025-09-28 09:40:34.906000
  - 2025-09-28 11:09:37.808000
  - 2025-09-29 03:39:59.445000
  - 2025-09-29 05:50:09.248000

### email
- **Data Type:** character varying
- **Description:** The email address to which the OTP was sent.
- **Business Use:** Identifies the recipient of the OTP.
- **How the Column Affects the Record:** Ensures the OTP is sent to the correct user.
- **Example Values:**
  - 0808snehakumari@gmail.com
  - Rakshithav1358@gmail.com
  - dakarangale02@gmail.com
  - dhirajkarangale02@gmail.com
  - harsh.kjs@gmail.com

### otp
- **Data Type:** character varying
- **Description:** The one-time password generated for the user.
- **Business Use:** Used for authentication purposes.
- **How the Column Affects the Record:** The actual OTP value that the user needs to enter for verification.
- **Example Values:**
  - 048218
  - 048322
  - 093988
  - 169848
  - 239419

## Primary Keys
- **id:** The primary key of the table, ensuring each record is unique.

## Foreign Keys
- **None:** This table does not have any foreign keys.

## Notes
- **Primary Key:** The `id` column is the primary key for this table.
- **Foreign Key Relationships:** There are no foreign key relationships defined for this table.