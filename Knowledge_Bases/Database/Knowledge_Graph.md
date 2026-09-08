# Knowledge Graph Representation

## Table Relationships
| Source Table | Target Table   | Relationship Type       | Details                                                                 |
|--------------|----------------|-------------------------|-------------------------------------------------------------------------|
| projects     | salespersons   | Foreign Key Reference  | `projects.salesperson` references `salespersons.id`                    |
| events       | salespersons   | Foreign Key Reference  | `events.salesperson` references `salespersons.id`                        |

## Column Relationships
| Source Column          | Target Column        | Relationship Type       | Details                                                                 |
|------------------------|----------------------|-------------------------|-------------------------------------------------------------------------|
| projects.salesperson   | salespersons.id      | Foreign Key Reference  | Direct reference establishing ownership/linkage                         |
| events.salesperson     | salespersons.id      | Foreign Key Reference  | Direct reference establishing ownership/linkage                         |

## Relationship Paths (up to 4 hops)
### Paths of length 1:
1. `projects` → `salespersons`  
   (via `projects.salesperson → salespersons.id`)
2. `events` → `salespersons`  
   (via `events.salesperson → salespersons.id`)

### Paths of length 2:
- None (No further connections from `salespersons` or intermediate tables)

### Paths of length 3:
- None (No chainable relationships)

### Paths of length 4:
- None (No chainable relationships)

## Isolation Notes
- Tables `otps` and `users` have no foreign key relationships with any other tables
- No relationships exist between `otps/users` and other tables in the schema
- `salespersons` has no outgoing foreign keys (only receives references)