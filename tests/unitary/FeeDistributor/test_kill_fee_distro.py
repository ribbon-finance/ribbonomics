import brownie
import pytest


@pytest.fixture(scope="module")
def fee_distributor(FeeDistributor, accounts, chain, voting_escrow, ve_rbn_rewards, weth):
    yield FeeDistributor.deploy(
        voting_escrow, chain.time(), weth, accounts[0], accounts[1], {"from": accounts[0]}
    )


def test_assumptions(fee_distributor, accounts):
    assert not fee_distributor.is_killed()
    assert fee_distributor.emergency_return() == accounts[1]


def test_kill(fee_distributor, accounts):
    fee_distributor.kill_me({"from": accounts[0]})

    assert fee_distributor.is_killed()


def test_multi_kill(fee_distributor, accounts):
    fee_distributor.kill_me({"from": accounts[0]})
    fee_distributor.kill_me({"from": accounts[0]})

    assert fee_distributor.is_killed()


def test_killing_xfers_tokens(fee_distributor, accounts, weth):
    accounts[3].transfer(fee_distributor, 31337)

    balanceBefore = accounts[1].balance()

    fee_distributor.kill_me({"from": accounts[0]})

    assert fee_distributor.emergency_return() == accounts[1]
    assert accounts[1].balance() - balanceBefore == 31337


def test_multi_kill_token_xfer(fee_distributor, accounts, weth):
    balanceBefore = accounts[1].balance()

    accounts[3].transfer(fee_distributor, 10000)
    fee_distributor.kill_me({"from": accounts[0]})

    accounts[3].transfer(fee_distributor, 30000)
    fee_distributor.kill_me({"from": accounts[0]})

    assert fee_distributor.emergency_return() == accounts[1]
    assert accounts[1].balance() - balanceBefore == 40000


@pytest.mark.parametrize("idx", range(1, 3))
def test_only_admin(fee_distributor, accounts, idx):
    with brownie.reverts():
        fee_distributor.kill_me({"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_after_killed(fee_distributor, accounts, idx):
    fee_distributor.kill_me({"from": accounts[0]})

    with brownie.reverts():
        fee_distributor.claim({"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_for_after_killed(fee_distributor, accounts, alice, idx):
    fee_distributor.kill_me({"from": accounts[0]})

    with brownie.reverts():
        fee_distributor.claim(alice, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_many_after_killed(fee_distributor, accounts, alice, idx):
    fee_distributor.kill_me({"from": accounts[0]})

    with brownie.reverts():
        fee_distributor.claim_many([alice] * 20, {"from": accounts[idx]})
