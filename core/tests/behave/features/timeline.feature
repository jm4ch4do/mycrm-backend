Feature: Timeline / Activity Feed
    As a CRM user
    I want to view a unified timeline of activities and notes
    So that I can see the complete engagement history for accounts, contacts, and deals

    Scenario: Account timeline shows all activity types
        Given I create "accounts" through the API
            | name      |
            | Acme Corp |
        And I create "tasks" through the API
            | title     | account_id |
            | Follow up | Acme Corp  |
        And I create "calls" through the API
            | title      | account_id | direction | outcome   |
            | Sales call | Acme Corp  | outbound  | connected |
        And I create "meetings" through the API
            | title        | account_id | outcome   |
            | Demo session | Acme Corp  | completed |
        And I create "notes" through the API
            | title        | content          | account_id | visibility |
            | Client notes | Great discussion | Acme Corp  | team       |

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200" and contains "4" records
        And the response contains
            | type    | title        |
            | task    | Follow up    |
            | call    | Sales call   |
            | meeting | Demo session |
            | note    | Client notes |

    Scenario: Timeline entries are sorted by created_at descending
        Given I create "accounts" through the API
            | name      |
            | Test Corp |
        And I create "tasks" through the API
            | title    | account_id |
            | Old task | Test Corp  |
        And I create "calls" through the API
            | title    | account_id | direction | outcome   |
            | New call | Test Corp  | outbound  | connected |
        And I create "notes" through the API
            | title       | content | account_id | visibility |
            | Recent note | Details | Test Corp  | team       |

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200"
        And the timeline is sorted by "created_at" descending

    Scenario: Contact timeline shows related activities and notes
        Given I create "accounts" through the API
            | name      |
            | Acme Corp |
        And I create "contacts" through the API
            | first_name | last_name | email         | account_id |
            | John       | Doe       | john@acme.com | Acme Corp  |
        And I create "tasks" through the API
            | title     | contact_id_from_email |
            | Call John | john@acme.com         |
        And I create "notes" through the API
            | title        | content       | contact_id_from_email | visibility |
            | John's prefs | Prefers email | john@acme.com         | team       |

        When I send a "GET" request to "/contacts/{contact.id}/timeline/"

        Then the response status code is "200" and contains "2" records
        And the response contains
            | type | title        |
            | task | Call John    |
            | note | John's prefs |

    Scenario: Deal timeline shows related activities and notes
        Given I create "accounts" through the API
            | name      |
            | Acme Corp |
        And I create "deals" through the API
            | name     | account_id | stage     |
            | Big Sale | Acme Corp  | qualified |
        And I create "meetings" through the API
            | title           | deal_id  | outcome   |
            | Contract review | Big Sale | completed |
        And I create "notes" through the API
            | title      | content        | deal_id  | visibility |
            | Deal notes | Key objections | Big Sale | team       |

        When I send a "GET" request to "/deals/{deal.id}/timeline/"

        Then the response status code is "200" and contains "2" records
        And the response contains
            | type    | title           |
            | meeting | Contract review |
            | note    | Deal notes      |

    Scenario: Filter timeline by type=note
        Given I create "accounts" through the API
            | name      |
            | Test Corp |
        And I create "tasks" through the API
            | title   | account_id |
            | My task | Test Corp  |
        And I create "notes" through the API
            | title  | content | account_id | visibility |
            | Note 1 | First   | Test Corp  | team       |
            | Note 2 | Second  | Test Corp  | team       |

        When I send a "GET" request to "/accounts/{account.id}/timeline/"
            | field | operator | value |
            | type  | eq       | note  |

        Then the response status code is "200" and contains "2" records
        And the response contains
            | type | title  |
            | note | Note 1 |
            | note | Note 2 |

    Scenario: Filter timeline by type=call
        Given I create "accounts" through the API
            | name      |
            | Test Corp |
        And I create "calls" through the API
            | title  | account_id | direction | outcome   |
            | Call 1 | Test Corp  | outbound  | connected |
        And I create "notes" through the API
            | title  | content | account_id | visibility |
            | Note 1 | Details | Test Corp  | team       |

        When I send a "GET" request to "/accounts/{account.id}/timeline/"
            | field | operator | value |
            | type  | eq       | call  |

        Then the response status code is "200" and contains "1" records
        And the response contains
            | type | title  |
            | call | Call 1 |

    Scenario: Soft-deleted activities are excluded from timeline
        Given I create "accounts" through the API
            | name      |
            | Test Corp |
        And I create "tasks" through the API
            | title        | account_id |
            | Deleted task | Test Corp  |
            | Active task  | Test Corp  |
        And I delete "activities" with "title" "Deleted task" using "soft delete"

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200" and contains "1" records
        And the response contains
            | type | title       |
            | task | Active task |

    Scenario: Private notes are hidden from other users
        Given I create "accounts" through the API
            | name      | owner_username |
            | Acme Corp | testuser1      |
        And I create "notes" through the API
            | title        | content | account_id | author_username | visibility |
            | Private note | Secret  | Acme Corp  | testuser1       | private    |
            | Team note    | Public  | Acme Corp  | testuser1       | team       |
        And I am "authenticated" as "a regular user"

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200" and contains "1" records
        And the response contains
            | type | title     |
            | note | Team note |

    Scenario: Private notes are visible to their author
        Given I create "accounts" through the API
            | name      |
            | Acme Corp |
        And I create "notes" through the API
            | title        | content       | account_id | visibility |
            | Private note | My own secret | Acme Corp  | private    |
            | Team note    | Public        | Acme Corp  | team       |

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200" and contains "2" records
        And the response contains
            | type | title        |
            | note | Private note |
            | note | Team note    |

    Scenario: Team notes are visible to other users
        Given I create "accounts" through the API
            | name      | owner_username |
            | Acme Corp | testuser1      |
        And I create "notes" through the API
            | title     | content | account_id | author_username | visibility |
            | Team note | Shared  | Acme Corp  | testuser1       | team       |
        And I am "authenticated" as "a regular user"

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200" and contains "1" records
        And the response contains
            | type | title     |
            | note | Team note |

    Scenario: Timeline returns 404 for non-existent entity
        Given I am "authenticated" as "a regular user"

        When I send a "GET" request to "/accounts/00000000-0000-0000-0000-000000000000/timeline/"

        Then the response status code is "404"

    Scenario: Timeline supports pagination
        Given I create "accounts" through the API
            | name      |
            | Test Corp |
        And I create "25" "tasks" for "account" "Test Corp"

        When I send a "GET" request to "/accounts/{account.id}/timeline/"

        Then the response status code is "200"
        And the response contains pagination with "20" results per page
