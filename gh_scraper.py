import requests
import re

def check_github_org(semester, course):
    """
    semester: e.g. 'F2021', 'W2022'
    course: e.g. 'ECSE223'
    """
    url = f"https://github.com/{semester}-{course}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return url
    return None

def scrape_all_combinations(start_year, end_year, course):
    """
    Tries all semester/year combos for a given course.
    """
    semesters = ["F", "W"]  # Fall, Winter, Summer
    found = []

    for year in range(start_year, end_year + 1):
        for sem in semesters:
            semester = f"{sem}{year}"
            result = check_github_org(semester, course)
            if result:
                print(f"Found: {result}")
                found.append(result)
            else:
                print(f"Not found: {semester}-{course}")

    return found

# Example usage
results = scrape_all_combinations(2015, 2025, "ECSE223")
print("\nAll found pages:", results)