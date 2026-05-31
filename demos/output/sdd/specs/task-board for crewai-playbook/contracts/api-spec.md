```yaml
openapi: 3.0.0
info:
  title: Task Board API Specification
  description: API contracts for managing tasks, playbooks, and crew assignments within the crewAI framework.
  version: 1.0.0
servers:
  - url: https://api.crewai.com/v1
    description: Production server URL

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    Task:
      type: object
      required:
        - task_id
        - name
        - description
        - assigned_role
        - status
      properties:
        task_id:
          type: string
          description: Unique identifier for the task.
          example: task-a1b2c3d4
        name:
          type: string
          description: User-friendly name of the task.
          example: Define API Contracts
        description:
          type: string
          description: Detailed description of the task scope.
          example: Generate OpenAPI documentation for the Task Board feature.
        assigned_role:
          type: string
          description: The team member (role) responsible for the task.
          enum: [Wukong, Bajie, Wujing, Longma, Manager]
          example: Bajie
        status:
          type: string
          description: Current status of the task.
          enum: [Pending, InProgress, Review, Completed, Blocked]
          example: InProgress
        priority:
          type: integer
          description: Priority level (1-5, 5 being highest).
          example: 4
    Playbook:
      type: object
      required:
        - playbook_id
        - name
        - steps
      properties:
        playbook_id:
          type: string
          description: Unique identifier for the playbook.
          example: pb-e5f6g7h8
        name:
          type: string
          description: Name of the playbook/workflow.
          example: System Setup Workflow
        steps:
          type: array
          items:
            type: object
            required:
              - step_name
              - description
              - required_skill
            properties:
              step_name:
                type: string
                description: Name of a specific step in the playbook.
              description:
                type: string
                description: Detailed action for the step.
              required_skill:
                type: string
                description: Skill needed (e.g., coding, analysis, documentation).
    Error:
      type: object
      properties:
        code:
          type: integer
          description: HTTP status code for the error.
        message:
          type: string
          description: Detailed error message.
        details:
          type: array
          items:
            type: string
            description: Specific failure points.

paths:
  /tasks:
    get:
      summary: Retrieve a list of all tasks for the team board.
      operationId: getTasks
      security:
        - BearerAuth: []
      requestBody:
        required: false
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Filter by task status (e.g., InProgress).
                  example: InProgress
                assigned_role:
                  type: string
                  description: Filter by assigned role.
                  example: Wujing
    post:
      summary: Create a new task on the board.
      operationId: createTask
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Task'
      responses:
        '201':
          description: Successfully created the task.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
        '400':
          description: Invalid input provided for the task creation.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /tasks/{task_id}:
    get:
      summary: Retrieve details for a specific task.
      operationId: getTaskById
      security:
        - BearerAuth: []
      parameters:
        - in: path
          name: task_id
          schema:
            type: string
            example: task-a1b2c3d4
      responses:
        '200':
          description: Successfully retrieved task details.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
        '404':
          description: Task not found.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
    put:
      summary: Update the status or details of an existing task.
      operationId: updateTask
      security:
        - BearerAuth: []
      parameters:
        - in: path
          name: task_id
          schema:
            type: string
            example: task-a1b2c3d4
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: New status (Pending, InProgress, Completed).
                  example: Completed
                assigned_role:
                  type: string
                  description: Reassign the task.
                  example: Wukong
      responses:
        '200':
          description: Task successfully updated.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
        '403':
          description: Forbidden - User does not have permission to modify this task.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
  /playbooks:
    get:
      summary: Retrieve a list of all defined playbooks/workflows.
      operationId: getPlaybooks
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Successfully retrieved list of playbooks.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Playbook'
    post:
      summary: Create a new playbook workflow.
      operationId: createPlaybook
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Playbook'
      responses:
        '201':
          description: Successfully created the playbook.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Playbook'
        '400':
          description: Invalid playbook structure.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```