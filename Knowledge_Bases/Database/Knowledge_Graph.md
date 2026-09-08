# Knowledge Graph Representation

## Table Relationships
| Source Table | Target Table   | Relationship Type       | Details                                                                 |
|--------------|----------------|-------------------------|-------------------------------------------------------------------------|
| projects     | salespersons   | Foreign Key Reference  | `projects.salesperson` references `salespersons.id`                    |
| events       | salespersons   | Foreign Key Reference  | `events.salesperson` references `salespersons.id`                        |
| salespersons | projects       | Array Reference        | `salespersons.projects[]` contains `projects.id`, creating a one-to-many relationship where one salesperson can manage multiple projects |

## Column Relationships
| Source Column          | Target Column        | Relationship Type       | Details                                                                 |
|------------------------|----------------------|-------------------------|-------------------------------------------------------------------------|
| projects.salesperson   | salespersons.id      | Foreign Key Reference  | Direct reference establishing ownership/linkage                         |
| events.salesperson     | salespersons.id      | Foreign Key Reference  | Direct reference establishing ownership/linkage                         |
| salespersons.projects[]| projects.id          | Array Reference        | Contains IDs of projects assigned to that salesperson                   |

## Relationship Paths (up to 4 hops)
### Paths of length 1:
1. `projects` → `salespersons`  
   (via `projects.salesperson → salespersons.id`)
2. `events` → `salespersons`  
   (via `events.salesperson → salespersons.id`)
3. `salespersons` → `projects`
   (via `salespersons.projects[] → projects.id`)

### Paths of length 2:
- None (No further connections from `salespersons` or intermediate tables)

### Paths of length 3:
- None (No chainable relationships)

### Paths of length 4:
- None (No chainable relationships)

## Isolation Notes
- `salespersons` acts as the central hub linking `projects` and `events`.