# Database Schema Overview

## Table List
- **projects**
- **events**
- **salespersons**

## Table Descriptions

### projects
- **Description**: This table stores information about projects.
- **Business Purpose**: Tracks and manages various projects, including their status and associated salesperson.
- **Details**:
  - **salesperson**: Identifier for the salesperson associated with the project.
  - **id**: Unique identifier for the project.
  - **created_at**: Timestamp of when the project was created.
  - **updated_at**: Timestamp of the last update to the project.
  - **project_name**: Name of the project.
  - **customer_name**: Name of the customer associated with the project.
  - **status**: Current status of the project.

### events
- **Description**: This table stores information about events related to projects.
- **Business Purpose**: Logs and tracks various events, such as meetings or updates, associated with projects and sales activities.
- **Details**:
  - **id**: Unique identifier for the event.
  - **salesperson**: Identifier for the salesperson associated with the event.
  - **data**: Additional data or details about the event.
  - **created_at**: Timestamp of when the event was created.
  - **updated_at**: Timestamp of the last update to the event.
  - **type**: Type of the event (e.g., meeting, call).
  - **participants**: List of participants in the event.
  - **customer_name**: Name of the customer associated with the event.
  - **project_name**: Name of the project associated with the event.
  - **summary**: Summary or notes about the event.

### salespersons
- **Description**: This table stores information about salespersons.
- **Business Purpose**: Manages and tracks salesperson details and their associated projects.
- **Details**:
  - **role**: Role of the salesperson within the organization.
  - **created_at**: Timestamp of when the salesperson's record was created.
  - **updated_at**: Timestamp of the last update to the salesperson's record.
  - **projects**: List of projects associated with the salesperson.
  - **id**: Unique identifier for the salesperson.
  - **email**: Email address of the salesperson.
  - **name**: Name of the salesperson.