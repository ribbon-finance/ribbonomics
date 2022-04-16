DAY = 86400
WEEK = 7 * DAY


def test_deposited_after(web3, chain, accounts, voting_escrow, ve_rbn_rewards, ve_rbn_rewards_st, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    for i in range(5):
        for j in range(7):
            token.transfer(ve_rbn_rewards, 10 ** 18, {"from": alice})
            ve_rbn_rewards.checkpoint_token()
            ve_rbn_rewards.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    voting_escrow.create_lock(amount, chain[-1].timestamp + 3 * WEEK, {"from": alice})
    chain.sleep(2 * WEEK)

    aliceBalanceBefore = token.balanceOf(alice)

    ve_rbn_rewards.claim({"from": alice})

    assert (token.balanceOf(alice) - aliceBalanceBefore) == 0


def test_deposited_during(web3, chain, accounts, voting_escrow, ve_rbn_rewards, ve_rbn_rewards_st, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    chain.sleep(WEEK)
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    ve_rbn_rewards_st = ve_rbn_rewards_st()

    for i in range(3):
        for j in range(7):
            token.transfer(ve_rbn_rewards_st, 10 ** 18, {"from": alice})
            ve_rbn_rewards_st.checkpoint_token()
            ve_rbn_rewards_st.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    ve_rbn_rewards_st.checkpoint_token()

    aliceBalanceBefore = token.balanceOf(alice)

    ve_rbn_rewards_st.claim({"from": alice})

    assert abs((token.balanceOf(alice) - aliceBalanceBefore) - 21 * 10 ** 18) < 10


def test_deposited_before(web3, chain, accounts, voting_escrow, ve_rbn_rewards, ve_rbn_rewards_st, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    ve_rbn_rewards_st = ve_rbn_rewards_st(t=start_time)
    token.transfer(ve_rbn_rewards_st, 10 ** 19, {"from": alice})
    ve_rbn_rewards_st.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards_st.checkpoint_token()

    aliceBalanceBefore = token.balanceOf(alice)

    ve_rbn_rewards_st.claim({"from": alice})

    assert abs((token.balanceOf(alice) - aliceBalanceBefore) - 10 ** 19) < 10

def test_deposited_twice(web3, chain, accounts, voting_escrow, ve_rbn_rewards, ve_rbn_rewards_st, token):
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

    ve_rbn_rewards_st = ve_rbn_rewards_st(t=start_time)
    token.transfer(ve_rbn_rewards_st, 10 * 10 ** 18, {"from": alice})
    ve_rbn_rewards_st.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards_st.checkpoint_token()

    aliceBalanceBefore = token.balanceOf(alice)

    ve_rbn_rewards_st.claim({"from": alice})

    tokens_to_exclude = ve_rbn_rewards_st.tokens_per_week(exclude_time)
    assert abs(10 ** 19 - (token.balanceOf(alice) - aliceBalanceBefore) - tokens_to_exclude) < 10


def test_deposited_parallel(web3, chain, accounts, voting_escrow, ve_rbn_rewards, ve_rbn_rewards_st, token):
    alice, bob, charlie = accounts[0:3]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})
    token.approve(voting_escrow.address, amount * 10, {"from": bob})
    token.transfer(bob, amount + 10 ** 19, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": bob})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    ve_rbn_rewards_st = ve_rbn_rewards_st(t=start_time)
    token.transfer(ve_rbn_rewards_st, 10 ** 19, {"from": alice})
    ve_rbn_rewards_st.checkpoint_token()
    chain.sleep(WEEK)
    ve_rbn_rewards_st.checkpoint_token()

    balance_before_alice = token.balanceOf(alice)
    balance_before_bob = token.balanceOf(bob)

    ve_rbn_rewards_st.claim({"from": alice})
    ve_rbn_rewards_st.claim({"from": bob})

    balance_alice = token.balanceOf(alice)
    balance_bob = token.balanceOf(bob)

    assert balance_alice - balance_before_alice == balance_bob - balance_before_bob
    assert abs(balance_alice + balance_bob - balance_before_alice - balance_before_bob - 10 ** 19) < 20
