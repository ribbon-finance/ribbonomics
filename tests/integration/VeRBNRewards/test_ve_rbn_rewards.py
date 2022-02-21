import pytest
from brownie import chain
import brownie

def test_ve_rbn_distribution(token, accounts, voting_escrow, whale, whale_amount, ve_rbn_rewards):
    token.transfer(whale, whale_amount, {"from": accounts[0]})
    token.approve(voting_escrow, whale_amount, {"from": whale})
    voting_escrow.create_lock(whale_amount, chain.time() + 3600 * 24 * 365, {"from": whale})
    rewards = 10**18
    token.approve(ve_rbn_rewards, rewards)
    ve_rbn_rewards.queueNewRewards(rewards, {"from": accounts[0]})
    assert ve_rbn_rewards.rewardRate() == rewards / 7 / 24 / 3600
    chain.sleep(3600)
    ve_rbn_rewards.getReward(False, {"from": whale})
    assert pytest.approx(token.balanceOf(whale), rel=10e-3) == rewards / 7 / 24
    chain.sleep(3600 * 24 * 7)
    ve_rbn_rewards.getReward(False, {"from": whale})
    assert pytest.approx(token.balanceOf(whale), rel=10e-3) == rewards


def test_ve_rbn_distribution_relock(
    token, accounts, voting_escrow, whale, whale_amount, ve_rbn_rewards
):
    token.transfer(whale, whale_amount, {"from": accounts[0]})
    token.approve(voting_escrow, whale_amount, {"from": whale})
    voting_escrow.create_lock(whale_amount, chain.time() + 3600 * 24 * 365, {"from": whale})
    rewards = 10**18
    token.approve(ve_rbn_rewards, rewards)
    ve_rbn_rewards.queueNewRewards(rewards, {"from": accounts[0]})
    assert ve_rbn_rewards.rewardRate() == rewards / 7 / 24 / 3600
    chain.sleep(3600)
    ve_rbn_rewards.getReward(True, {"from": whale})
    assert pytest.approx(voting_escrow.locked(whale)[0]) == rewards / 7 / 24 + whale_amount
    chain.sleep(3600 * 24 * 7)
    ve_rbn_rewards.getReward(True, {"from": whale})
    assert pytest.approx(voting_escrow.locked(whale)[0]) == rewards + whale_amount


def test_sweep(token, accounts, voting_escrow, ve_rbn_rewards, create_token, whale, whale_amount):
    token.transfer(whale, whale_amount, {"from": accounts[0]})
    token.approve(voting_escrow, whale_amount, {"from": whale})
    voting_escrow.create_lock(whale_amount, chain.time() + 3600 * 24 * 365, {"from": whale})
    yfo = create_token("YFO")
    yfo.transfer(ve_rbn_rewards, 10**18, {"from": accounts[0]})
    balance_after = yfo.balanceOf(accounts[0])
    with brownie.reverts("!authorized"):
        ve_rbn_rewards.sweep(yfo, {"from": whale})
    with brownie.reverts("!rewardToken"):
        ve_rbn_rewards.sweep(token, {"from": accounts[0]})
    ve_rbn_rewards.sweep(yfo, {"from": accounts[0]})
    assert yfo.balanceOf(accounts[0]) == balance_after + 10**18
