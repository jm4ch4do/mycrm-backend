Feature: User Management
    As a CRM system
    I want to manage users and their CRM roles
    So that access control and role-based behaviour works correctly

    Scenario: User profile is auto-created on user creation
        Given I create a new "user"
            | username | password    |
            | roleuser | testpass123 |
        Then the "user" with "username" "roleuser" has a related "profile"

    Scenario Outline: Update user role enforces staff-only access
        Given I create a new "user"
            | username | password    |
            | <target> | testpass123 |
        And I am "authenticated" as "<auth>"
        When I send a "PUT" request to "/users/{<target>.id}/" with body
            | field | value  |
            | role  | <role> |
        Then the response status code is "<status>"

        Examples:
            | target      | auth           | role    | status |
            | targetuser  | a staff user   | manager | 200    |
            | targetuser2 | a regular user | admin   | 403    |

    Scenario: User list - unauthenticated access is forbidden
        Given I am "not authenticated"
        When I send a "GET" request to "/users/"
        Then the response status code is "403"

    Scenario: User list - authenticated users have access
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/users/"
        Then the response status code is "200"

    Scenario: Authenticated user list response includes role field
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/users/"
        Then every item in the response has field "role"

    Scenario: GET /me/ returns current user with role
        Given I am "authenticated" as "a regular user"
        When I send a "GET" request to "/me/"
        Then the response status code is "200"
        And the response contains field "role"
        And the response contains field "username"

    Scenario: GET /me/ requires authentication
        Given I am "not authenticated"
        When I send a "GET" request to "/me/"
        Then the response status code is "403"
