import brownie


def test_commit_admin_only(voting_escrow, accounts):
    with brownie.reverts("dev: admin only"):
        voting_escrow.commit_transfer_ownership(accounts[1], {"from": accounts[1]})

def test_apply_admin_only(voting_escrow, accounts):
    with brownie.reverts("dev: admin only"):
        voting_escrow.apply_transfer_ownership({"from": accounts[1]})

def test_set_funds_locked_admin_only(voting_escrow, accounts):
    with brownie.reverts("dev: admin only"):
        voting_escrow.set_funds_unlocked(true, {"from": accounts[1]})

def test_set_reward_pool_admin_only(voting_escrow, ve_rbn_rewards, accounts):
    with brownie.reverts("dev: admin only"):
        voting_escrow.set_reward_pool(ve_rbn_rewards, {"from": accounts[1]})

def test_commit_transfer_ownership(voting_escrow, accounts):
    voting_escrow.commit_transfer_ownership(accounts[1], {"from": accounts[0]})

    assert voting_escrow.admin() == accounts[0]
    assert voting_escrow.future_admin() == accounts[1]


def test_apply_transfer_ownership(voting_escrow, accounts):
    voting_escrow.commit_transfer_ownership(accounts[1], {"from": accounts[0]})
    voting_escrow.apply_transfer_ownership({"from": accounts[0]})

    assert voting_escrow.admin() == accounts[1]

def test_set_funds_locked_admin_only(voting_escrow, accounts):
    voting_escrow.set_funds_unlocked(True, {"from": accounts[0]})

    assert voting_escrow.is_unlocked() == True

    voting_escrow.set_funds_unlocked(False, {"from": accounts[0]})

    assert voting_escrow.is_unlocked() == False

def test_apply_without_commit(voting_escrow, accounts):
    with brownie.reverts("dev: admin not set"):
        voting_escrow.apply_transfer_ownership({"from": accounts[0]})
