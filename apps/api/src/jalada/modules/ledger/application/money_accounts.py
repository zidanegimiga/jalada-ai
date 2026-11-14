from jalada.modules.accounts.domain.users import User
from jalada.modules.ledger.domain.money_accounts import default_accounts
from jalada.unit_of_work import UnitOfWork


def open_default_accounts(work: UnitOfWork, user: User) -> None:
    """Gives a new user the accounts everyone starts with. Runs when a user is created."""
    accounts = work.money_accounts_for(user.id)
    for account in default_accounts(user.id, user.created_at):
        accounts.add(account)
