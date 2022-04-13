from brownie import ZERO_ADDRESS

WEEK = 86400 * 7


def test_claimable(alice, bob, charlie, accounts, chain, voting_escrow, ve_rbn_rewards, token):
    amount = 1000 * 10 ** 18

    for acct in (alice, bob, charlie):
        token.approve(voting_escrow, amount * 10, {"from": acct})
        token.transfer(acct, amount, {"from": alice})
        voting_escrow.create_lock(amount, chain.time() + 8 * WEEK, {"from": acct})

    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    ve_rbn_rewards = ve_rbn_rewards(t=start_time)
    token.transfer(ve_rbn_rewards, amount, {"from": alice})
    ve_rbn_rewards.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards.checkpoint_token()

    ve_rbn_rewards.claim_many([alice, bob, charlie] + [ZERO_ADDRESS] * 17, {"from": alice})

    balances = [token.balanceOf(i) for i in (alice, bob, charlie)]
    chain.undo()
    assert ve_rbn_rewards.claim(alice {"from": alice}).return_value == ve_rbn_rewards.claimable(bob, {"from": bob})
