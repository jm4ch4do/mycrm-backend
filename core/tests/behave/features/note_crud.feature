Feature: Note CRUD Operations
    As a CRM user
    I want to manage notes through the API
    So that I can capture information linked to accounts, contacts, and deals

    Background:
        Given I create "accounts" through the API
            | name      | status |
            | Acme Corp | active |

    Scenario: Create and list notes
        Given I create "notes" through the API
            | title           | body              | account_id |
            | Client Feedback | Great interaction | Acme Corp  |
            | Follow-up Info  | Call next week    | Acme Corp  |
            | General Note    | Important details | Acme Corp  |
        When I send a "GET" request to "/notes/"
        Then the response status code is "200" and contains "3" records
        And the response contains
            | title           |
            | Client Feedback |
            | Follow-up Info  |
            | General Note    |

    Scenario: Filter by visibility
        Given I create a new "note"
            | title        | body         | account_id | visibility |
            | Private Note | Private info | Acme Corp  | private    |
            | Team Note    | Team info    | Acme Corp  | team       |
            | Public Note  | Public info  | Acme Corp  | public     |
        When I send a "GET" request to "/notes/"
            | field      | operator | value   |
            | visibility | eq       | private |
        Then the response status code is "200" and contains "1" records
        And the response should contain details
            | title        |
            | Private Note |

    Scenario: Filter by is_pinned
        Given I create a new "note"
            | title       | body         | account_id | is_pinned |
            | Pinned Note | Important    | Acme Corp  | true      |
            | Normal Note | Regular info | Acme Corp  | false     |
        When I send a "GET" request to "/notes/"
            | field     | operator | value |
            | is_pinned | eq       | true  |
        Then the response status code is "200" and contains "1" records
        And the response should contain details
            | title       |
            | Pinned Note |

    Scenario: Retrieve single note details
        Given I create a new "note"
            | title        | body             | account_id | visibility |
            | Detail Check | Full information | Acme Corp  | team       |
        When I request details for "notes" with "title" "Detail Check"
        Then the response status code is "200"
        And the response should contain details
            | title        | body             | visibility |
            | Detail Check | Full information | team       |

    Scenario: Update note fields
        Given I create a new "note"
            | title     | body        | account_id | visibility |
            | Update Me | Old content | Acme Corp  | private    |
        When I update "notes" with "title" "Update Me"
            | body        | visibility |
            | New content | public     |
        Then the "note" with "title" "Update Me" should have "body" "New content"
        And the "note" with "title" "Update Me" should have "visibility" "public"

    Scenario: Soft delete note
        Given I create a new "note"
            | title     | body       | account_id |
            | Delete Me | Some notes | Acme Corp  |
        When I soft delete "notes" with "title" "Delete Me"
        Then the "note" with "title" "Delete Me" should not appear in the list

    Scenario: Other user cannot modify note
        Given I create a new "note"
            | title      | body         | account_id |
            | Owner Note | Confidential | Acme Corp  |
        And I am "authenticated" as "a regular user"
        When I update "notes" with "title" "Owner Note"
            | body   |
            | Hacked |
        Then the response status code is "403"

    Scenario: Author field is read-only on update
        Given I create a new "note"
            | title         | body      | account_id |
            | Original Note | Some text | Acme Corp  |
        When I update "notes" with "title" "Original Note"
            | body         | author_username |
            | Updated text | hacker          |
        Then the "note" with "title" "Original Note" should have "body" "Updated text"
        And the "note" with "title" "Original Note" should have "author" "testuser"
