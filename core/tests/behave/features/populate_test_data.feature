Feature: Populate Test Data
    As a developer
    I want to populate the database with test data
    So that I can have a consistent test environment

    Scenario: Populate database with default test accounts
        Given I create "accounts" through the API
            | name           | status   | type     | owner_username |
            | Acme Corp      | prospect | customer | testuser1      |
            | Tech Solutions | active   | partner  | testuser1      |
            | Global Trade   | inactive | vendor   | testuser2      |
