print("\n=== Testing Python utility ===")
from passcore_util import PassCoreUtility

print("\n=== PYTHON VAULT: ===")
print(PassCoreUtility.vault_health())

print("\n=== PYTHON IMAGES: ===")
print(PassCoreUtility.images_health())

print("\n\n=== Testing C# utility ===")

from passcore_util import PassCoreUtility

utility = PassCoreUtility()

try:
    print("\n=== VAULT HEALTH ===")

    vault = utility.vault_health()

    print(vault)

    print("\n=== IMAGES HEALTH ===")

    images = utility.images_health()

    print(images)

    print("=== TEST 1: No changes ===")

    result = utility.create_backup(
        force=False
    )
    print(result)

    print("\n=== TEST 2: Mark changed ===")

    result = utility.mark_vault_changed()

    print(result)

    print("\n=== TEST 3: Backup after change ===")

    result = utility.create_backup(
        force=True
    )
    print(result)

    print("\n=== TEST 4: Backup again ===")

    result = utility.create_backup(
        force=False
    )
    print(result)

finally:
    utility.close()