from brownie import ZERO_ADDRESS

WEEK = 86400 * 7


def test_claimable(alice, bob, charlie, chain, voting_escrow, ve_rbn_rewards, fee_distributor, coin_a, token):
    amount = 1000 * 10 ** 18

    for acct in (alice, bob, charlie):
        token.approve(voting_escrow, amount * 10, {"from": acct})
        token.transfer(acct, amount, {"from": alice})
        voting_escrow.create_lock(amount, chain.time() + 8 * WEEK, {"from": acct})

    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    fee_distributor = fee_distributor(t=start_time)
    coin_a._mint_for_testing(fee_distributor, 10 ** 19)
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    fee_distributor.claim_many([alice, bob, charlie] + [ZERO_ADDRESS] * 17, {"from": alice})

    balances = [coin_a.balanceOf(i) for i in (alice, bob, charlie)]
    chain.undo()

    assert fee_distributor.claim({"from": alice}) == fee_distributor.claimable({"from": bob})
