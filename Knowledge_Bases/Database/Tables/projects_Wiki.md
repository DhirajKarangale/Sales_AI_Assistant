# Projects Table

The `projects` table stores information about various projects managed by the organization. Each project is associated with a salesperson and contains details such as the project name, customer, and status.

## Columns

### salesperson
- **Type:** uuid
- **Description:** Unique identifier for the salesperson responsible for the project.
- **Business Use:** Identifies the salesperson who is managing or responsible for the project.
- **How it affects the record:** Links the project to a specific salesperson, ensuring accountability and tracking of responsibilities.
- **Example Values:**
  - ec37371f-22f8-4cec-bbd0-74d162bfe67c
  - 99ff091f-bf2c-429d-a556-22f59525412f
  - f52f2cff-2e14-4da5-9c85-3f8114d0d5d6
  - 09cfdc46-a939-4899-8a40-17cda3f97786
  - 710c8ecf-6340-4edf-a4e9-06513d500a59

### id
- **Type:** uuid
- **Description:** Unique identifier for the project.
- **Business Use:** Uniquely identifies each project within the system.
- **How it affects the record:** Ensures that each project can be uniquely referenced and managed.
- **Example Values:**
  - a3622281-2413-41da-b8e9-0e6e2580606f
  - 9101b2de-d408-4645-93ff-6296678b7da8
  - 59482a35-e455-4180-9de4-2d55d2f3654a
  - c892e32e-2cc2-4b99-9885-db2720e34467
  - a8265c87-09d3-4a13-9fc8-706ac892dda4

### created_at
- **Type:** timestamp with time zone
- **Description:** Timestamp indicating when the project record was created.
- **Business Use:** Tracks the creation date and time of the project record, useful for audit and historical purposes.
- **How it affects the record:** Provides a timestamp for when the project was initially recorded in the system.
- **Example Values:**
  - 2026-09-08 17:36:38.891202+00:00

### updated_at
- **Type:** timestamp with time zone
- **Description:** Timestamp indicating the last time the project record was updated.
- **Business Use:** Tracks the last modification date and time of the project record, useful for audit and historical purposes.
- **How it affects the record:** Provides a timestamp for the last update made to the project record.
- **Example Values:**
  - 2026-09-08 17:36:38.891202+00:00

### project_name
- **Type:** character varying
- **Description:** Name of the project.
- **Business Use:** Identifies the project by a human-readable name.
- **How it affects the record:** Provides a meaningful label for the project to stakeholders.
- **Example Values:**
  - Customer Portal
  - AI Analytics Platform
  - CRM Migration
  - ERP Integration
  - Security Platform

### customer_name
- **Type:** character varying
- **Description:** Name of the customer for whom the project is being executed.
- **Business Use:** Identifies the client or customer associated with the project.
- **How it affects the record:** Links the project to a specific customer, ensuring proper billing and communication.
- **Example Values:**
  - PayFlow
  - DataSphere
  - PeopleFirst
  - Acme Corp
  - GlobalMart

### status
- **Type:** character varying
- **Description:** Current status of the project.
- **Business Use:** Tracks the progress and current state of the project.
- **How it affects the record:** Indicates whether the project is ongoing, completed, on hold, or closed, which impacts project management and resource allocation.
- **Example Values:**
  - ongoing
  - closed
  - completed
  - hold

## Primary Keys

- **id**: The primary key for the `projects` table, ensuring each project has a unique identifier.

## Foreign Keys

- **salesperson**: Foreign key that references the `id` column in the `salespersons` table, establishing a relationship between a project and the salesperson responsible for it.

## Relationships

- **salesperson** (Foreign Key):
  - **Foreign Table:** salespersons
  - **Foreign Column:** id
  - **Description:** Links each project to a specific salesperson, allowing tracking of salesperson activities and responsibilities.