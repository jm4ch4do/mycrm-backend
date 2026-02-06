Feature: Account CRUD Operations
    As a CRM user
    I want to manage accounts through the API
    So that I can track customer information

    Scenario: Create and list accounts
        Given I create "accounts" through the API
            | name           | status   | type     | owner_username |
            | Acme Corp      | prospect | customer | testuser1      |
            | Tech Solutions | active   | partner  | testuser1      |
            | Global Trade   | inactive | vendor   | testuser2      |

        When I send a "GET" request to "/accounts/"

        Then the response status code is "200" and contains "3" records
        And the response contains
            | name           | status   | type     |
            | Acme Corp      | prospect | customer |
            | Tech Solutions | active   | partner  |
            | Global Trade   | inactive | vendor   |

    Scenario: Filter accounts by status
        Given I create "accounts" through the API
            | name        | status   | type     | owner_username |
            | Active Co   | active   | customer | testuser1      |
            | Prospect Co | prospect | customer | testuser1      |
            | Lost Co     | lost     | customer | testuser1      |

        When I send a "GET" request to "/accounts/"
            | field  | operator | value  |
            | status | eq       | active |

        Then the response status code is "200" and contains "1" records
        And the first account should have name "Active Co"

    Scenario: Update account status
        Given I create "accounts" through the API
            | name      |
            | Test Corp |

        When I update the account "Test Corp" status to "active"

        Then the account "Test Corp" should have status "active"

    Scenario: Retrieve single account details
        Given I create "accounts" through the API
            | name        | status | type     | owner_username | industry | website             |
            | Detail Corp | active | customer | testuser1      | Software | https://example.com |

        When I request details for account "Detail Corp"

        Then the response should contain account details
            | name        | status | type     | industry | website             |
            | Detail Corp | active | customer | Software | https://example.com |

    Scenario: Create multiple accounts with defaults
        Given I generate "100" "accounts" through the API

        When I send a "GET" request to "/accounts/?page_size=100"

        Then the response status code is "200" and contains "100" records
