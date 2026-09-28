"""Education access rules shared by the views and their visible controls."""


def can_manage_education(user):
    """Only the active portfolio owner may create or delete records."""
    return user.is_authenticated and user.is_active and user.is_superuser


def can_edit_education(user):
    """Editor membership is managed through Django Admin, never public input."""
    return can_manage_education(user) or (
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name="Editor").exists()
    )


def education_access_context(user):
    can_manage = can_manage_education(user)
    can_edit = can_edit_education(user)
    if can_manage:
        role = "Owner"
    elif can_edit:
        role = "Editor"
    elif user.is_authenticated:
        role = "Member"
    else:
        role = "Visitor"
    return {
        "can_manage_education": can_manage,
        "can_edit_education": can_edit,
        "education_role": role,
    }
