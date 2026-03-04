Feature: Contact CRUD Operations
    As a CRM user
    I want to manage contacts through the API
    So that I can track individuals at my accounts

    Scenario: Create and list contacts
        Given I create "accounts" through the API
            | name           | status |
            | Acme Corp      | active |
            | Tech Solutions | active |
        And I create "contacts" through the API
            | first_name | last_name | email         | account_id   | role           | seniority |
            | John       | Doe       | john@acme.com | Acme Corp    | decision_maker | senior    |
            | Jane       | Smith     | jane@tech.com | Tech Solutions | influencer   | junior    |
            | Bob        | Johnson   | bob@acme.com  | Acme Corp    | user           | junior    |
        When I send a "GET" request to "/contacts/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | first_name | last_name | email         |
            | John       | Doe       | john@acme.com |
            | Jane       | Smith     | jane@tech.com |
            | Bob        | Johnson   | bob@acme.com  |

    Scenario: Filter contacts by role
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |
        And I create "contacts" through the API
            | first_name | last_name | email            | account_id | role           | seniority |
            | Alice      | Brown     | alice@acme.com   | Acme Corp  | decision_maker | senior    |
            | Charlie    | Davis     | charlie@acme.com | Acme Corp  | influencer     | junior    |
            | Diana      | Evans     | diana@acme.com   | Acme Corp  | user           | junior    |
            | Edward     | Fox       | edward@acme.com  | Acme Corp  | decision_maker | executive |
        When I send a "GET" request to "/contacts/"
            | field | operator | value          |
            | role  | eq       | decision_maker |
        Then the response status code is "200" and contains "2" records

    Scenario: Filter contacts by seniority
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |
        And I create "contacts" through the API
            | first_name | last_name | email            | account_id_from_name | role       | seniority |
            | Alice      | Brown     | alice@acme.com   | Acme Corp            | influencer | senior    |
            | Bob        | Clark     | bob@acme.com     | Acme Corp            | user       | senior    |
            | Charlie    | Davis     | charlie@acme.com | Acme Corp            | influencer | executive |
            | Diana      | Evans     | diana@acme.com   | Acme Corp            | user       | junior    |
        When I send a "GET" request to "/contacts/"
            | field     | operator | value  |
            | seniority | eq       | senior |
        Then the response status code is "200" and contains "2" records

    Scenario: Filter contacts by account
        Given I create "accounts" through the API
            | name           | status |
            | Acme Corp      | active |
            | Tech Solutions | active |
        And I create "contacts" through the API
            | first_name | last_name | email         | account_id     | role       | seniority |
            | John       | Doe       | john@acme.com | Acme Corp      | influencer | senior    |
            | Jane       | Smith     | jane@acme.com | Acme Corp      | user       | executive |
            | Bob        | Johnson   | bob@tech.com  | Tech Solutions | influencer | junior    |
        When I request details for "contacts" by "account_id" "Acme Corp"
        Then the response status code is "200" and contains "2" records

    Scenario: Retrieve single contact details
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |
        And I create "contacts" through the API
            | first_name | last_name | email         | account_id_from_name | role           | seniority | job_title   | department | phone    | mobile   |
            | Jane       | Smith     | jane@acme.com | Acme Corp            | decision_maker | senior    | VP of Sales | Sales      | 555-1234 | 555-5678 |
        When I request details for "contacts" with "email" "jane@acme.com"
        Then the response status code is "200"
        And the response should contain account details
            | first_name | last_name | email         | role           | seniority | job_title   | department | phone    | mobile   |
            | Jane       | Smith     | jane@acme.com | decision_maker | senior    | VP of Sales | Sales      | 555-1234 | 555-5678 |

    Scenario: Create multiple contacts with defaults
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |
        And I generate "50" "contacts" with "account_id" "Acme Corp" through the API
        When I send a "GET" request to "/contacts/?page_size=50"
        Then the response status code is "200" and contains "50" records

    Scenario: Search contacts by name
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |
        And I create "contacts" through the API
            | first_name | last_name | email             | account_id_from_name | role | seniority |
            | John       | Smith     | jsmith@acme.com   | Acme Corp            | user | junior    |
            | Jane       | Johnson   | jjohnson@acme.com | Acme Corp            | user | executive |
            | Bob        | Smith     | bsmith@acme.com   | Acme Corp            | user | senior    |
        When I send a "GET" request to "/contacts/"
            | field  | operator | value |
            | search | eq       | Smith |
        Then the response status code is "200" and contains "2" records
