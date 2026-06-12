"""Step definitions for user management BDD tests."""

from django.contrib.auth import get_user_model

from steps.utils import store_entity_on_context


def create_users_from_table(context):
    """
    Create user(s) directly in the database from the step table.

    Each row produces one User. The ``password`` column, if present, is popped
    and applied via ``set_password()`` so the value is properly hashed. The
    value in the first column is used as the context label: stored via
    ``setattr(context, label, user)`` for URL placeholder resolution and in
    ``context.named_users`` for domain-specific Then steps.
    """

    user_model = get_user_model()
    for row in context.table:
        data = {key: value for key, value in row.items()}
        password = data.pop("password", None)
        tid = data.pop("_tid", None)
        user = user_model.objects.create(**data)
        if password is not None:
            user.set_password(password)
            user.save(update_fields=["password"])

        label = data[context.table.headings[0]]
        store_entity_on_context(context, "user", user, tid=tid)
        setattr(context, label, user)
        if not hasattr(context, "named_users"):
            context.named_users = {}
        context.named_users[label] = user
