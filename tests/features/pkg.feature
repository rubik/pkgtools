Feature: Testing the pkg module

Scenario Outline: Test SDist object
    Given I set sdist to "itertools_recipes-0.1.tar.gz" as SDist
    When I get sdist.<attr>
    Then I see <result>

    Examples:
        | attr         | result                             |
        | name         | itertools-recipes                  |
        | version      | 0.1                                |
        | as_req       | itertools-recipes==0.1             |
        | has_metadata | True                               |
        | zip_safe     | True                               |
        | location     | *dist/itertools_recipes-0.1.tar.gz |


Scenario Outline: Test Egg object
    Given I set egg_dist to "pkgtools-0.6.2-py2.7.egg" as Egg
    When I get egg_dist.<attr>
    Then I see <result>

    Examples:
        | attr         | result                         |
        | name         | pkgtools                       |
        | version      | 0.6.2                          |
        | as_req       | pkgtools==0.6.2                |
        | has_metadata | True                           |
        | zip_safe     | False                          |
        | location     | *dist/pkgtools-0.6.2-py2.7.egg |

Scenario Outline: Test Dir object
    Given I set dir_dist to "pkgtools.egg-info" as Dir
    When I get dir_dist.<attr>
    Then I see <result>

    Examples:
        | attr         | result                  |
        | name         | pkgtools                |
        | version      | 0.6.2                   |
        | as_req       | pkgtools==0.6.2         |
        | has_metadata | True                    |
        | zip_safe     | True                    |
        | location     | *dist/pkgtools.egg-info |

Scenario Outline: Test Dir object with a fake dist
    Given I set dir_test to "fakedist.egg-info" as Dir
    When I get dir_test.<attr>
    Then I see <result>

    Examples:
        | attr         | result                  |
        | name         | fakedist                |
        | version      | 0.0.0                   |
        | as_req       | fakedist==0.0.0         |
        | has_metadata | True                    |
        | zip_safe     | False                   |
        | location     | *dist/fakedist.egg-info |