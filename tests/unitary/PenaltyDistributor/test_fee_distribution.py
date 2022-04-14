DAY = 86400
WEEK = 7 * DAY


def test_deposited_after(web3, chain, accounts, voting_escrow, ve_rbn_rewards, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18
    ve_rbn_rewards = ve_rbn_rewards()

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    for i in range(5):
        for j in range(7):
            token.transfer(ve_rbn_rewards, 10 ** 18, {"from": bob})
            ve_rbn_rewards.checkpoint_token()
            ve_rbn_rewards.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    voting_escrow.create_lock(amount, chain[-1].timestamp + 3 * WEEK, {"from": alice})
    chain.sleep(2 * WEEK)

    ve_rbn_rewards.claim({"from": alice})

    assert token.balanceOf(alice) == 0


def test_deposited_during(web3, chain, accounts, voting_escrow, ve_rbn_rewards, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    chain.sleep(WEEK)
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    ve_rbn_rewards = ve_rbn_rewards()

    for i in range(3):
        for j in range(7):
            token.transfer(ve_rbn_rewards, 10 ** 18, {"from": bob})
            ve_rbn_rewards.checkpoint_token()
            ve_rbn_rewards.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    ve_rbn_rewards.checkpoint_token()

    ve_rbn_rewards.claim({"from": alice})

    assert abs(token.balanceOf(alice) - 21 * 10 ** 18) < 10


def test_deposited_before(web3, chain, accounts, voting_escrow, ve_rbn_rewards, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    ve_rbn_rewards = ve_rbn_rewards(t=start_time)
    token.transfer(ve_rbn_rewards, 10 ** 19, {"from": bob})
    ve_rbn_rewards.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards.checkpoint_token()

    ve_rbn_rewards.claim({"from": alice})

    assert abs(coin_a.balanceOf(alice) - 10 ** 19) < 10

def test_deposited_twice(web3, chain, accounts, voting_escrow, ve_rbn_rewards, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 4 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 3)
    voting_escrow.withdraw({"from": alice})
    exclude_time = chain[-1].timestamp // WEEK * WEEK  # Alice had 0 here
    voting_escrow.create_lock(amount, chain[-1].timestamp + 4 * WEEK, {"from": alice})
    chain.sleep(WEEK * 2)

    ve_rbn_rewards = ve_rbn_rewards(t=start_time)
    token.transfer(ve_rbn_rewards, 10 ** 18, {"from": bob})
    ve_rbn_rewards.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards.checkpoint_token()

    ve_rbn_rewards.claim({"from": alice})

    tokens_to_exclude = ve_rbn_rewards.tokens_per_week(exclude_time)
    assert abs(10 ** 19 - token.balanceOf(alice) - tokens_to_exclude) < 10


def test_deposited_parallel(web3, chain, accounts, voting_escrow, ve_rbn_rewards, token):
    alice, bob, charlie = accounts[0:3]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    token.approve(voting_escrow.address, amount * 10, {"from": bob})
    token.transfer(bob, amount, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": bob})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    ve_rbn_rewards = ve_rbn_rewards(t=start_time)
    token.transfer(fee_distributor, 10 ** 19, {"from": charlie})
    ve_rbn_rewards.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards.checkpoint_token()

    ve_rbn_rewards.claim({"from": alice})
    ve_rbn_rewards.claim({"from": bob})

    balance_alice = token.balanceOf(alice)
    balance_bob = token.balanceOf(bob)

    assert balance_alice == balance_bob
    assert abs(balance_alice + balance_bob - 10 ** 19) < 20
