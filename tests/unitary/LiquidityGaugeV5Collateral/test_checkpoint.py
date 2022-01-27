import brownie

YEAR = 86400 * 365


def test_user_checkpoint(accounts, gauge_v5_collateral):
    gauge_v5_collateral.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_new_period(accounts, chain, gauge_v5_collateral):
    gauge_v5_collateral.user_checkpoint(accounts[1], {"from": accounts[1]})
    chain.sleep(int(YEAR * 1.1))
    gauge_v5_collateral.user_checkpoint(accounts[1], {"from": accounts[1]})


def test_user_checkpoint_wrong_account(accounts, gauge_v5_collateral):
    with brownie.reverts("dev: unauthorized"):
        gauge_v5_collateral.user_checkpoint(accounts[2], {"from": accounts[1]})
