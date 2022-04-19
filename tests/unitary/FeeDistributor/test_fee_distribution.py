DAY = 86400
WEEK = 7 * DAY


def test_deposited_after(web3, chain, accounts, voting_escrow, ve_rbn_rewards, fee_distributor, weth, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18
    fee_distributor = fee_distributor()

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    for i in range(5):
        for j in range(7):
            accounts[3].transfer(fee_distributor, "1 ether")
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    chain.mine()

    voting_escrow.create_lock(amount, chain[-1].timestamp + 3 * WEEK, {"from": alice})
    chain.sleep(2 * WEEK)

    aliceBalanceBefore = alice.balance()

    fee_distributor.claim({"from": alice})

    assert alice.balance() == aliceBalanceBefore


def test_deposited_during(web3, chain, accounts, voting_escrow, ve_rbn_rewards, fee_distributor, weth, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    chain.sleep(WEEK)
    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    fee_distributor = fee_distributor()

    for i in range(3):
        for j in range(7):
            accounts[3].transfer(fee_distributor, "1 ether")
            fee_distributor.checkpoint_token()
            fee_distributor.checkpoint_total_supply()
            chain.sleep(DAY)
            chain.mine()

    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    aliceBalanceBefore = alice.balance()

    fee_distributor.claim({"from": alice})

    assert abs((alice.balance() - aliceBalanceBefore) - 21 * 10 ** 18) < 10


def test_deposited_before(web3, chain, accounts, voting_escrow,ve_rbn_rewards, fee_distributor, weth, token):
    alice, bob = accounts[0:2]
    amount = 1000 * 10 ** 18

    token.approve(voting_escrow.address, amount * 10, {"from": alice})

    voting_escrow.create_lock(amount, chain[-1].timestamp + 8 * WEEK, {"from": alice})
    chain.sleep(WEEK)
    chain.mine()
    start_time = int(chain.time())
    chain.sleep(WEEK * 5)

    fee_distributor = fee_distributor(t=start_time)
    accounts[3].transfer(fee_distributor, "10 ether")
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    aliceBalanceBefore = alice.balance()

    fee_distributor.claim({"from": alice})

    assert abs((alice.balance() - aliceBalanceBefore) - 10 ** 19) < 10

def test_deposited_twice(web3, chain, accounts, voting_escrow, ve_rbn_rewards, fee_distributor, weth, token):
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

    fee_distributor = fee_distributor(t=start_time)
    accounts[3].transfer(fee_distributor, "10 ether")
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    aliceBalanceBefore = alice.balance()

    fee_distributor.claim({"from": alice})

    tokens_to_exclude = fee_distributor.tokens_per_week(exclude_time)
    assert abs(10 ** 19 - (alice.balance() - aliceBalanceBefore) - tokens_to_exclude) < 10


def test_deposited_parallel(web3, chain, accounts, voting_escrow, ve_rbn_rewards, fee_distributor, weth, token):
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

    fee_distributor = fee_distributor(t=start_time)
    accounts[3].transfer(fee_distributor, "10 ether")
    fee_distributor.checkpoint_token()
    chain.sleep(WEEK)
    fee_distributor.checkpoint_token()

    aliceBalanceBefore = alice.balance()
    bobBalanceBefore = bob.balance()

    fee_distributor.claim({"from": alice})
    fee_distributor.claim({"from": bob})

    balance_alice = alice.balance()
    balance_bob = bob.balance()
    assert balance_alice == balance_bob
    assert abs((balance_alice-aliceBalanceBefore) + (balance_bob-bobBalanceBefore) - 10 ** 19) < 20
