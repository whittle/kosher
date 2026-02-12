"""Hardcoded Gherkin steps for the login scenario."""

STEPS = [
    'Given I am on the test page at "http://127.0.0.1:8765/test_page.html"',
    'When I type "user@example.com" into the "Email" field',
    'When I type "secret123" into the "Password" field',
    'When I click the "Login" button',
    'Then I should see the text "Welcome"',
    'Then I should see the text "user@example.com"',
]
