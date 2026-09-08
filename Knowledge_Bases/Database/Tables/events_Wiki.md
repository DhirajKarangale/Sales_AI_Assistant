# Events Table Wiki

## Table Description
The `events` table captures various types of events related to sales activities, meetings, and other interactions. Each event is associated with a salesperson and includes details such as the type of event, participants, customer name, project name, and a summary. The table also tracks when each event was created and last updated.

## Columns

### id
- **Data Type**: uuid
- **Description**: A unique identifier for each event.
- **Business Use**: Serves as the primary key to uniquely identify each event record.
- **How it Affects the Record**: Ensures that each event can be uniquely referenced in the database.
- **Example Values**:
  - 59c807af-0036-442a-be5d-3fc8129267e3
  - fc35fac2-2066-4481-891f-74c6411c0efe
  - 468da382-21d1-4625-bbc3-01f2cfbb1155
  - f6f41fbc-92b0-4b61-babb-23e27e129989
  - cb4bd374-01f4-49d8-8874-d5286f67bcca

### salesperson
- **Data Type**: uuid
- **Description**: The unique identifier of the salesperson associated with the event.
- **Business Use**: Links the event to a specific salesperson, allowing for tracking of their activities.
- **How it Affects the Record**: Establishes a relationship with the `salespersons` table to identify the salesperson responsible for the event.
- **Example Values**:
  - ec37371f-22f8-4cec-bbd0-74d162bfe67c
  - 99ff091f-bf2c-429d-a556-22f59525412f
  - f52f2cff-2e14-4da5-9c85-3f8114d0d5d6
  - 09cfdc46-a939-4899-8a40-17cda3f97786
  - 710c8ecf-6340-4edf-a4e9-06513d500a59

### data
- **Data Type**: jsonb
- **Description**: Additional data related to the event, stored in JSON format.
- **Business Use**: Contains supplementary information that may vary depending on the event type.
- **How it Affects the Record**: Provides flexibility for storing event-specific data without requiring a fixed schema.
- **Example Values**: Not Available

### created_at
- **Data Type**: timestamp with time zone
- **Description**: The timestamp indicating when the event record was created.
- **Business Use**: Tracks the creation time of the event for historical and audit purposes.
- **How it Affects the Record**: Helps in understanding when the event was first recorded in the system.
- **Example Values**:
  - 2026-09-08 17:47:04.826774+00:00
  - 2026-09-08 17:46:43.125352+00:00
  - 2026-09-08 17:46:02.928320+00:00

### updated_at
- **Data Type**: timestamp with time zone
- **Description**: The timestamp indicating when the event record was last updated.
- **Business Use**: Tracks the last modification time of the event for historical and audit purposes.
- **How it Affects the Record**: Helps in understanding when the event details were last changed.
- **Example Values**:
  - 2026-09-08 17:47:04.826774+00:00
  - 2026-09-08 17:46:43.125352+00:00
  - 2026-09-08 17:46:02.928320+00:00

### type
- **Data Type**: USER-DEFINED
- **Description**: The type of event.
- **Business Use**: Classifies the event into different categories to facilitate filtering and reporting.
- **How it Affects the Record**: Determines the nature of the event and influences how it is processed and displayed.
- **Example Values**:
  - meeting
  - mail
  - calendar_event

### participants
- **Data Type**: ARRAY
- **Description**: A list of participants involved in the event.
- **Business Use**: Tracks who was involved in the event, useful for collaboration and follow-up.
- **How it Affects the Record**: Provides context on the attendees and helps in managing communication and responsibilities.
- **Example Values**:
  - ['Evelyn Wright', 'Ethan King']
  - ['Amelia Hall', 'Alexander Walker']
  - ['Daniel Thomas', 'Olivia Martin']
  - ['Sophia Moore', 'Michael Taylor']
  - ['William Jackson', 'Emma White']

### customer_name
- **Data Type**: character varying
- **Description**: The name of the customer associated with the event.
- **Business Use**: Identifies the customer for whom the event was conducted.
- **How it Affects the Record**: Links the event to a specific customer, facilitating customer management and follow-up.
- **Example Values**:
  - TechNova
  - HealthPlus
  - PayFlow
  - PeopleFirst
  - Acme Corp

### project_name
- **Data Type**: character varying
- **Description**: The name of the project associated with the event.
- **Business Use**: Identifies the project for which the event was conducted.
- **How it Affects the Record**: Links the event to a specific project, facilitating project management and tracking.
- **Example Values**:
  - Security Platform
  - AI Analytics Platform
  - CRM Migration
  - Customer Portal
  - Data Warehouse

### summary
- **Data Type**: text
- **Description**: A brief summary of the event.
- **Business Use**: Provides a quick overview of the event's content or outcome.
- **How it Affects the Record**: Offers a concise description that can be used for quick reference and reporting.
- **Example Values**: Not Available

## Primary Keys
- **id**: The primary key for the `events` table, ensuring each event is uniquely identified.

## Foreign Keys
- **Column**: salesperson
  - **Foreign Table**: salespersons
  - **Foreign Column**: id
  - **Description**: Establishes a relationship between the `events` table and the `salespersons` table, linking each event to a specific salesperson.