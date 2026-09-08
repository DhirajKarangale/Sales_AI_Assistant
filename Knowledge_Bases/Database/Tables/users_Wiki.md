# Users Table Wiki

## Table Description
The `users` table stores information about registered users in the system. It includes details such as user ID, creation timestamp, number of entries, username, email, and a brief description about the user.

## Columns

### id
- **Data Type**: integer
- **Description**: Unique identifier for each user.
- **Business Use**: Used to uniquely identify users in the system.
- **How it Affects the Record**: Ensures that each user has a unique identifier, which is essential for database operations and relationships.
- **Example Values**: 
  - 1
  - 2
  - 3
  - 4
  - 5

### created_at
- **Data Type**: timestamp without time zone
- **Description**: Timestamp indicating when the user record was created.
- **Business Use**: Tracks the date and time when a user was registered in the system.
- **How it Affects the Record**: Helps in auditing and understanding user activity over time.
- **Example Values**: 
  - 2025-09-30 03:05:43.295000
  - 2025-09-29 06:52:21.111000
  - 2025-09-29 10:14:45.984000
  - 2025-09-26 16:33:07.366000
  - 2025-10-05 13:27:23.933000

### entriescount
- **Data Type**: integer
- **Description**: Number of entries or contributions made by the user.
- **Business Use**: Tracks user activity and engagement within the system.
- **How it Affects the Record**: Provides a metric to measure user participation and can be used for ranking or rewards.
- **Example Values**: 
  - 3
  - 0
  - 2
  - 1

### username
- **Data Type**: character varying
- **Description**: Username chosen by the user.
- **Business Use**: Displays the username for user identification and communication.
- **How it Affects the Record**: Ensures a unique and recognizable name for each user, which is used in various interactions.
- **Example Values**: 
  - Jaadu
  - DKode
  - Ravithreni 
  - Dhiraj Karangale
  - Rakshitha V

### email
- **Data Type**: character varying
- **Description**: Email address of the user.
- **Business Use**: Used for communication, authentication, and verification.
- **How it Affects the Record**: Essential for user verification and account recovery.
- **Example Values**: 
  - dakarangale02@gmail.com
  - 0808snehakumari@gmail.com
  - vaibhavhonkalse110@gmail.com
  - momotek975@bitmens.com
  - Rakshithav1358@gmail.com

### about
- **Data Type**: text
- **Description**: A brief description about the user.
- **Business Use**: Allows users to provide additional information about themselves.
- **How it Affects the Record**: Enhances user profiles and can be used for personalization or community building.
- **Example Values**: 
  - I am alien
  - I am Ravithreni 
  - Full Stack Developer with MERN stack. Skilled in building responsive UI/UX, optimizing performance, and delivering scalable products.
  - student
  - hi , i am human

## Primary Keys
- **id**: The primary key of the `users` table, ensuring each user has a unique identifier.

## Foreign Keys
- **None**: The `users` table does not have any foreign keys.

## Additional Notes
- **Foreign Key Relationships**: Not Available
- **Business Logic**: Not Available