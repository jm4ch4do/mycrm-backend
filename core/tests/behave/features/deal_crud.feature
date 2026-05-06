Feature: Deal CRUD Operations
    As a CRM user
    I want to manage deals through the API
    So that I can track sales opportunities in my pipeline

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list deals
        Given I create "accounts" through the API
            | name           | status |
            | Tech Solutions | active |
        And I create "deals" through the API
            | name            | account_id     | stage    | status | amount   | currency |
            | Enterprise Deal | Acme Corp      | proposal | open   | 50000.00 | usd      |
            | Starter Deal    | Tech Solutions | lead     | open   | 10000.00 | eur      |
            | Big Deal        | Acme Corp      | won      | won    | 99000.00 | usd      |
        When I send a "GET" request to "/deals/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | name            | stage    | status |
            | Enterprise Deal | proposal | open   |
            | Starter Deal    | lead     | open   |
            | Big Deal        | won      | won    |

    Scenario: Filter deals by stage
        Given I create "deals" through the API
            | name   | account_id | stage       | status |
            | Deal A | Acme Corp  | lead        | open   |
            | Deal B | Acme Corp  | proposal    | open   |
            | Deal C | Acme Corp  | lead        | open   |
            | Deal D | Acme Corp  | negotiation | open   |
        When I send a "GET" request to "/deals/"
            | field | operator | value |
            | stage | eq       | lead  |
        Then the response status code is "200" and contains "2" records

    Scenario: Filter deals by account
        Given I create "accounts" through the API
            | name           | status |
            | Tech Solutions | active |
        And I create "deals" through the API
            | name   | account_id     | stage | status |
            | Deal A | Acme Corp      | lead  | open   |
            | Deal B | Tech Solutions | lead  | open   |
            | Deal C | Acme Corp      | lead  | open   |
        When I request details for "deals" by "account_id" "Acme Corp"
        Then the response status code is "200" and contains "2" records

    Scenario: Update deal details
        Given I create "deals" through the API
            | name        | account_id | stage | status | amount   |
            | Update Deal | Acme Corp  | lead  | open   | 10000.00 |
        When I update "deals" with "name" "Update Deal"
            | stage       | amount   |
            | negotiation | 25000.00 |
        Then the "deal" with "name" "Update Deal" should have "stage" "negotiation"

    Scenario: Retrieve single deal details
        Given I create "deals" through the API
            | name        | account_id | stage    | status | amount   | currency | probability | lead_source |
            | Detail Deal | Acme Corp  | proposal | open   | 75000.00 | usd      | 60          | inbound     |
        When I request details for "deal" with "name" "Detail Deal"
        Then the response status code is "200"
        And the response should contain details
            | name        | stage    | status | amount   | currency | lead_source |
            | Detail Deal | proposal | open   | 75000.00 | usd      | inbound     |

    Scenario: Soft delete deal
        Given I create "deals" through the API
            | name        | account_id | stage | status |
            | Delete Deal | Acme Corp  | lead  | open   |
        When I soft delete "deals" with "name" "Delete Deal"
        Then the "deal" with "name" "Delete Deal" should not appear in the list

    Scenario: Add contact to deal
        Given I create "contacts" through the API
            | first_name | last_name | email         | account_id |
            | John       | Doe       | john@acme.com | Acme Corp  |
        And I create "deals" through the API
            | name       | account_id | stage | status |
            | Assoc Deal | Acme Corp  | lead  | open   |
        When I add contact "john@acme.com" to "deal" with "name" "Assoc Deal"
        Then the response status code is "201"

    Scenario: Remove contact from deal
        Given I create "contacts" through the API
            | first_name | last_name | email         | account_id |
            | Jane       | Smith     | jane@acme.com | Acme Corp  |
        And I create "deals" through the API
            | name        | account_id | stage | status |
            | Remove Deal | Acme Corp  | lead  | open   |
        And I add contact "jane@acme.com" to "deal" with "name" "Remove Deal"
        When I remove contact "jane@acme.com" from "deal" with "name" "Remove Deal"
        Then the response status code is "204"

    Scenario: Create multiple deals with defaults
        Given I generate "50" "deals" with "account_id" "Acme Corp" through the API
        When I send a "GET" request to "/deals/?page_size=50"
        Then the response status code is "200" and contains "50" records
