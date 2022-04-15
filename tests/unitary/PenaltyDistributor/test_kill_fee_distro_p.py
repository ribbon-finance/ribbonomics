import brownie
import pytest


@pytest.fixture(scope="module")
def ve_rbn_rewards(PenaltyDistributor, accounts, chain, voting_escrow, token):
    yield PenaltyDistributor.deploy(
        voting_escrow, chain.time(), token, accounts[0], accounts[1], {"from": accounts[0]}
    )


def test_assumptions(ve_rbn_rewards, accounts):
    assert not ve_rbn_rewards.is_killed()
    assert ve_rbn_rewards.emergency_return() == accounts[1]


def test_kill(ve_rbn_rewards, accounts):
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    assert ve_rbn_rewards.is_killed()


def test_multi_kill(ve_rbn_rewards, accounts):
    ve_rbn_rewards.kill_me({"from": accounts[0]})
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    assert ve_rbn_rewards.is_killed()


def test_killing_xfers_tokens(ve_rbn_rewards, accounts, weth):
    accounts[3].transfer(ve_rbn_rewards, 31337)

    balanceBefore = accounts[1].balance()

    ve_rbn_rewards.kill_me({"from": accounts[0]})

    assert ve_rbn_rewards.emergency_return() == accounts[1]
    assert accounts[1].balance() - balanceBefore == 31337


def test_multi_kill_token_xfer(ve_rbn_rewards, accounts, weth):
    balanceBefore = accounts[1].balance()

    accounts[3].transfer(ve_rbn_rewards, 10000)
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    accounts[3].transfer(ve_rbn_rewards, 30000)
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    assert ve_rbn_rewards.emergency_return() == accounts[1]
    assert accounts[1].balance() - balanceBefore == 40000


@pytest.mark.parametrize("idx", range(1, 3))
def test_only_admin(ve_rbn_rewards, accounts, idx):
    with brownie.reverts():
        ve_rbn_rewards.kill_me({"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_after_killed(ve_rbn_rewards, accounts, idx):
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    with brownie.reverts():
        ve_rbn_rewards.claim({"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_for_after_killed(ve_rbn_rewards, accounts, alice, idx):
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    with brownie.reverts():
        ve_rbn_rewards.claim(alice, {"from": accounts[idx]})


@pytest.mark.parametrize("idx", range(1, 3))
def test_cannot_claim_many_after_killed(ve_rbn_rewards, accounts, alice, idx):
    ve_rbn_rewards.kill_me({"from": accounts[0]})

    with brownie.reverts():
        ve_rbn_rewards.claim_many([alice] * 20, {"from": accounts[idx]})
