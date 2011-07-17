Feature: Testing the pkg module

Scenario Outline: Test SDist object
    Given I set sdist to "itertools_recipes-0.1.tar.gz" as SDist
    When I get sdist.<attr>
    Then I see <result>

    Examples:
        | attr         | result                 |
        | name         | itertools-recipes      |
        | version      | 0.1                    |
        | as_req       | itertools-recipes==0.1 |
        | has_metadata | True                   |
        | zip_safe     | True                   |


Scenario Outline: Test Egg object
    Given I set egg_dist to "pkgtools-0.6.2-py2.7.egg" as Egg
    When I get egg_dist.<attr>
    Then I see <result>

    Examples:
        | attr         | result          |
        | name         | pkgtools        |
        | version      | 0.6.2           |
        | as_req       | pkgtools==0.6.2 |
        | has_metadata | True            |
        | zip_safe     | False           |