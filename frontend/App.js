import React, { useState, useEffect, useRef } from "react";
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Animated,
  SafeAreaView,
  StatusBar,
  Linking,
  Alert
} from "react-native";
import { api, BACKEND_IP, PORT } from "./api";

// Design Tokens (Handloom Dye Theme)
const COLORS = {
  bg: "#FAF6EE",           // Warm Natural Beige
  ink: "#211A2E",          // Deep Indigo Black
  inkSoft: "#4A4457",      // Soft Purple Slate
  muted: "#837B8C",        // Warm Muted Gray
  border: "rgba(33, 26, 46, 0.12)",
  borderStrong: "rgba(33, 26, 46, 0.22)",
  
  red: "#B8503F",          // Madder Root Red (Repayments, Alerts)
  redSoft: "#F3E1DC",
  gold: "#C08A2C",         // Turmeric Gold (Monsoon savings, warnings)
  goldSoft: "#F4E8D2",
  teal: "#0E5C5B",         // Petrol Teal (Primary Action buttons)
  tealSoft: "#DCEBE9",
  moss: "#57724F",         // Moss Green (credits, safe balances)
  mossSoft: "#E4EBDF"
};

export default function App() {
  const [activeTab, setActiveTab] = useState("wallet");
  
  // App State
  const [weaverData, setWeaverData] = useState(null);
  const [walletData, setWalletData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  
  // Inputs
  const [loanAmount, setLoanAmount] = useState("3000");
  const [saleAmount, setSaleAmount] = useState("10000");
  const [saleDesc, setSaleDesc] = useState("Bulk Varanasi Silk Saree order");
  
  // Animations
  const [isWeaving, setIsWeaving] = useState(false);
  const shuttleAnim = useRef(new Animated.Value(0)).current;
  const threadAnim = useRef(new Animated.Value(0)).current;
  
  // Custom split banner feedback
  const [splitFeedback, setSplitFeedback] = useState(null);
  
  // Fetch dashboard data
  const fetchData = async () => {
    try {
      setApiError(null);
      const [weaver, wallet] = await Promise.all([
        api.getWeaver(),
        api.getWallet()
      ]);
      setWeaverData(weaver);
      setWalletData(wallet);
    } catch (err) {
      console.error(err);
      setApiError(err.message || "Failed to connect to KarigarPay Backend. Make sure your local server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Run the loom shuttle thread weaving animation
  const runWeavingAnimation = (onComplete) => {
    setIsWeaving(true);
    shuttleAnim.setValue(0);
    threadAnim.setValue(0);
    
    Animated.parallel([
      Animated.timing(shuttleAnim, {
        toValue: 1,
        duration: 1500,
        useNativeDriver: false,
      }),
      Animated.timing(threadAnim, {
        toValue: 100,
        duration: 1500,
        useNativeDriver: false,
      })
    ]).start(() => {
      setIsWeaving(false);
      onComplete();
    });
  };

  // Actions
  const handleBuyYarn = async () => {
    const amt = parseFloat(loanAmount);
    if (isNaN(amt) || amt <= 0) {
      Alert.alert("Invalid Amount", "Please enter a valid loan amount.");
      return;
    }
    
    setLoading(true);
    try {
      // Disburse loan via API
      runWeavingAnimation(async () => {
        try {
          const res = await api.buyYarn(amt);
          Alert.alert("Loom Loan Approved!", res.message);
          fetchData();
        } catch (err) {
          Alert.alert("Loan Rejected", err.message);
          setLoading(false);
        }
      });
    } catch (err) {
      Alert.alert("Disbursement Error", err.message);
      setLoading(false);
    }
  };

  const handleSimulateSale = async (amountVal, descVal) => {
    const amt = parseFloat(amountVal || saleAmount);
    const desc = descVal || saleDesc;
    if (isNaN(amt) || amt <= 0) {
      Alert.alert("Invalid Amount", "Please enter a valid sale amount.");
      return;
    }
    
    setLoading(true);
    try {
      const res = await api.simulateSale(amt, desc);
      setSplitFeedback(res.message);
      // clear notification after 6 seconds
      setTimeout(() => setSplitFeedback(null), 6000);
      fetchData();
    } catch (err) {
      Alert.alert("Simulation Error", err.message);
      setLoading(false);
    }
  };

  const handleToggleInsurance = async (checked) => {
    setLoading(true);
    try {
      const res = await api.toggleInsurance(checked);
      Alert.alert("Loom Suraksha Update", res.message);
      fetchData();
    } catch (err) {
      Alert.alert("Insurance Error", err.message);
      setLoading(false);
    }
  };

  const handleSimulateMonth = async () => {
    setLoading(true);
    try {
      const res = await api.simulateMonth();
      Alert.alert("Month Simulated", res.message);
      fetchData();
    } catch (err) {
      Alert.alert("Insurance Error", err.message);
      setLoading(false);
    }
  };

  const handleFileClaim = async (type) => {
    setLoading(true);
    try {
      const res = await api.fileClaim(type);
      Alert.alert("Loom Suraksha Payout Released!", res.message);
      fetchData();
    } catch (err) {
      Alert.alert("Claim Filing Error", err.message);
      setLoading(false);
    }
  };

  const handleResetDB = async () => {
    Alert.alert(
      "Reset Prototype",
      "Are you sure you want to reset the database to starting seed state?",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Yes, Reset", 
          style: "destructive",
          onPress: async () => {
            setLoading(true);
            try {
              const res = await api.resetDatabase();
              setSplitFeedback(null);
              Alert.alert("Reset Complete", res.message);
              fetchData();
            } catch (err) {
              Alert.alert("Reset Error", err.message);
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  if (apiError) {
    return (
      <SafeAreaView style={styles.errorContainer}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.errorCard}>
          <Text style={styles.errorTitle}>🔌 Connection Failure</Text>
          <Text style={styles.errorText}>{apiError}</Text>
          <Text style={styles.errorHint}>
            Currently configured Backend IP: {BACKEND_IP}:{PORT}{"\n\n"}
            If you are running this app on a physical device, make sure both your phone and development PC are connected to the same Wi-Fi network, and that you have replaced BACKEND_IP in frontend/api.js with your computer's local network IP.
          </Text>
          <TouchableOpacity style={styles.errorBtn} onPress={fetchData}>
            <Text style={styles.errorBtnText}>Retry Connection</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Derived state helper variables
  const walletBalance = walletData?.wallet_balance ?? 3200;
  const monsoonSavings = walletData?.monsoon_savings_balance ?? 0;
  const lciScore = weaverData?.lci?.score ?? 600;
  const lciBand = weaverData?.lci?.band ?? "Good";
  const activeLoan = weaverData?.active_loan;
  const loanLimit = weaverData?.lci?.loan_limit ?? 37000;
  const enrolledSuraksha = weaverData?.profile?.loom_suraksha_enrolled ?? false;
  const ledger = walletData?.ledger ?? [];

  return (
    <SafeAreaView style={styles.safeContainer}>
      <StatusBar barStyle="dark-content" />
      
      {/* Shell Header */}
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <View style={styles.brandMark}>
            <Text style={styles.brandMarkText}>🌾</Text>
          </View>
          <View>
            <Text style={styles.brandName}>Karigar Pay</Text>
            <Text style={styles.brandTag}>Weaver Neobank</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchData}>
          <Text style={styles.refreshBtnText}>↺ Sync</Text>
        </TouchableOpacity>
      </View>

      {/* Horizontal Status Strip */}
      <View style={styles.statusStripContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.statusStrip}>
          <View style={styles.statusChip}>
            <View style={[styles.statusDot, { backgroundColor: COLORS.moss }]} />
            <Text style={styles.statusChipText}>Wallet: <Text style={styles.statusBold}>₹{walletBalance.toLocaleString("en-IN")}</Text></Text>
          </View>
          <View style={styles.statusChip}>
            <View style={[styles.statusDot, { backgroundColor: COLORS.teal }]} />
            <Text style={styles.statusChipText}>LCI: <Text style={styles.statusBold}>{lciScore}</Text> · {lciBand}</Text>
          </View>
          <View style={[styles.statusChip, !activeLoan && styles.chipDimmed]}>
            <View style={[styles.statusDot, { backgroundColor: COLORS.red }]} />
            <Text style={styles.statusChipText}>Loan: <Text style={styles.statusBold}>{activeLoan ? `₹${activeLoan.outstanding_balance} due` : "none"}</Text></Text>
          </View>
          <View style={[styles.statusChip, !enrolledSuraksha && styles.chipDimmed]}>
            <View style={[styles.statusDot, { backgroundColor: COLORS.gold }]} />
            <Text style={styles.statusChipText}>Suraksha: <Text style={styles.statusBold}>{enrolledSuraksha ? "enrolled" : "off"}</Text></Text>
          </View>
        </ScrollView>
      </View>

      {/* Live Transaction / Action Floating Banners */}
      {splitFeedback && (
        <View style={styles.splitFeedbackBanner}>
          <Text style={styles.splitFeedbackTitle}>⚡ Split Flow Fired</Text>
          <Text style={styles.splitFeedbackText}>{splitFeedback}</Text>
        </View>
      )}

      {/* Main Tab Views */}
      <ScrollView style={styles.scrollContainer} contentContainerStyle={styles.scrollContent}>
        {loading && <ActivityIndicator size="large" color={COLORS.teal} style={styles.globalLoader} />}

        {/* 1. WALLET TAB */}
        {activeTab === "wallet" && (
          <View style={styles.viewContent}>
            <Text style={styles.viewEyebrow}>Module 1 · Digital Payments</Text>
            <Text style={styles.viewTitle}>Karigar Wallet</Text>
            <Text style={styles.viewSub}>
              Direct settlements, verifiable income logs, and automated sweeps.
            </Text>

            {/* Wallet Card */}
            <View style={styles.walletHero}>
              <View style={styles.walletHeroTop}>
                <View>
                  <Text style={styles.walletLabel}>AVAILABLE BALANCE</Text>
                  <Text style={styles.walletBalance}>₹{walletBalance.toLocaleString("en-IN")}</Text>
                </View>
                <View style={styles.walletChipContainer}>
                  <Text style={styles.walletLabel}>LINKED CARD</Text>
                  <View style={styles.walletCardChip} />
                </View>
              </View>
              <Text style={styles.walletAccount}>
                VA · 4218 9903 KGRP  ·  RuPay •••• 7742
              </Text>
            </View>

            {/* Monsoon Reserve Vault Info */}
            <View style={styles.savingsVaultCard}>
              <View style={styles.savingsVaultHeader}>
                <Text style={styles.savingsVaultIcon}>🐷</Text>
                <View>
                  <Text style={styles.savingsVaultTitle}>Monsoon Reserve Vault</Text>
                  <Text style={styles.savingsVaultSubtitle}>Automated off-season savings</Text>
                </View>
              </View>
              <Text style={styles.savingsVaultBalance}>
                ₹{monsoonSavings.toLocaleString("en-IN")}
              </Text>
              <Text style={styles.savingsVaultHint}>
                5% of all incoming payment transfers are swept automatically into this interest-bearing savings sub-account.
              </Text>
            </View>

            {/* Simulate Payments */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Simulate Cooperative Payout</Text>
              <Text style={styles.cardDesc}>
                Mock a cooperative settlement and watch the LCI auto-split flow handle loan repayment and Monsoon Reserve sweep.
              </Text>
              <View style={styles.simControls}>
                <TouchableOpacity 
                  style={[styles.btn, { backgroundColor: COLORS.teal }]} 
                  onPress={() => handleSimulateSale(1200, "Varanasi Silk SHG Saree Order")}
                >
                  <Text style={styles.btnText}>₹1,200 · Saree Order</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.btn, styles.btnOutline]} 
                  onPress={() => handleSimulateSale(2600, "Bulk Silk fabric Regional Marketplace")}
                >
                  <Text style={styles.btnOutlineText}>₹2,600 · Bulk Order</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.btn, styles.btnOutline]} 
                  onPress={() => handleSimulateSale(450, "Local Bazaar retail purchase")}
                >
                  <Text style={styles.btnOutlineText}>₹450 · Retail Sale</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Transaction Ledger */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Recent Transactions</Text>
              {ledger.length === 0 ? (
                <Text style={styles.emptyLedger}>No transaction logs yet.</Text>
              ) : (
                ledger.map((tx) => {
                  const isCredit = tx.type === "CR";
                  const isLoan = tx.type === "LN";
                  
                  return (
                    <View key={tx.tx_id} style={styles.ledgerRow}>
                      <View style={styles.ledgerInfo}>
                        <Text style={styles.ledgerDesc}>{tx.description}</Text>
                        <Text style={styles.ledgerTime}>
                          {tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : ""}
                        </Text>
                      </View>
                      <Text style={[
                        styles.ledgerAmount,
                        isCredit && styles.ledgerCredit,
                        !isCredit && !isLoan && styles.ledgerDebit,
                        isLoan && styles.ledgerNeutral
                      ]}>
                        {isCredit ? "+" : isLoan ? "" : "−"}₹{tx.amount}
                      </Text>
                    </View>
                  );
                })
              )}
            </View>
          </View>
        )}

        {/* 2. LOOM LOAN TAB */}
        {activeTab === "loan" && (
          <View style={styles.viewContent}>
            <Text style={styles.viewEyebrow}>Module 2 · Micro-Credit</Text>
            <Text style={styles.viewTitle}>Loom Loan</Text>
            <Text style={styles.viewSub}>
              Credit scoring checks your production consistency and unlocks instant capital.
            </Text>

            {/* Credit limit meter */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Pre-approved Loan Limit</Text>
              
              <View style={styles.limitTrack}>
                <View style={[
                  styles.limitFill, 
                  { width: `${Math.min(100, ((loanLimit - 3000) / 47000) * 100)}%` }
                ]} />
              </View>
              
              <View style={styles.limitLabels}>
                <Text style={styles.limitLabelMin}>Min: ₹3,000</Text>
                <Text style={styles.limitLabelMax}>Max: ₹50,000</Text>
              </View>
              
              <View style={styles.limitDetails}>
                <Text style={styles.limitDetailsText}>Pre-approved Limit:</Text>
                <Text style={styles.limitDetailsVal}>₹{loanLimit.toLocaleString("en-IN")}</Text>
              </View>

              <View style={styles.formField}>
                <Text style={styles.formLabel}>Buy Yarn (Enter amount to disburse)</Text>
                <TextInput
                  style={styles.formInput}
                  keyboardType="numeric"
                  value={loanAmount}
                  onChangeText={setLoanAmount}
                  placeholder="e.g. 3000"
                />
                <Text style={styles.formHint}>
                  Yarn capital routes directly to the cooperative raw-material supplier (does not enter your wallet balance).
                </Text>
              </View>

              <TouchableOpacity 
                style={[styles.btn, { backgroundColor: COLORS.ink }]} 
                onPress={handleBuyYarn}
                disabled={isWeaving}
              >
                <Text style={styles.btnText}>Buy Yarn — Disburse Instantly</Text>
              </TouchableOpacity>

              {/* Shuttle Loader Animation */}
              {isWeaving && (
                <View style={styles.shuttleLoader}>
                  <Text style={styles.shuttleLoaderText}>Weaving yarn contract...</Text>
                  <View style={styles.shuttleTrack}>
                    <Animated.View style={[
                      styles.shuttleThread,
                      {
                        width: threadAnim.interpolate({
                          inputRange: [0, 100],
                          outputRange: ["0%", "100%"]
                        })
                      }
                    ]} />
                    <Animated.View style={[
                      styles.shuttleBlock,
                      {
                        left: shuttleAnim.interpolate({
                          inputRange: [0, 1],
                          outputRange: ["-10%", "105%"]
                        })
                      }
                    ]} />
                  </View>
                </View>
              )}
            </View>

            {/* Active Loan Status */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Active Loan Status</Text>
              {!activeLoan ? (
                <Text style={styles.emptyLedger}>No active loom loans found. Raise a yarn order to disburse.</Text>
              ) : (
                <View style={styles.loanStatusCard}>
                  <View style={styles.loanStatusRow}>
                    <Text style={styles.loanStatusLabel}>Principal Loan Amount</Text>
                    <Text style={styles.loanStatusVal}>₹{activeLoan.principal}</Text>
                  </View>
                  <View style={styles.loanStatusRow}>
                    <Text style={styles.loanStatusLabel}>Outstanding Balance</Text>
                    <Text style={[styles.loanStatusVal, { color: COLORS.red }]}>₹{activeLoan.outstanding_balance}</Text>
                  </View>
                  <View style={styles.loanStatusRow}>
                    <Text style={styles.loanStatusLabel}>Escrow Split Share</Text>
                    <Text style={styles.loanStatusVal}>{activeLoan.emi_split_percentage}% of each sale</Text>
                  </View>
                </View>
              )}
            </View>
          </View>
        )}

        {/* 3. LCI CREDIT ENGINE TAB */}
        {activeTab === "lci" && (
          <View style={styles.viewContent}>
            <Text style={styles.viewEyebrow}>Module 5 · Credit Scoring</Text>
            <Text style={styles.viewTitle}>Livelihood Capital Index</Text>
            <Text style={styles.viewSub}>
              Our proprietary scoring system calculates credit worthiness using actual production logs instead of traditional bank proxies.
            </Text>

            {/* Score Display Card */}
            <View style={styles.card}>
              <View style={styles.scoreDialCenter}>
                <Text style={styles.scoreNumber}>{lciScore}</Text>
                <View style={[
                  styles.scoreBadge, 
                  { backgroundColor: 
                      lciBand === "Excellent" ? COLORS.mossSoft :
                      lciBand === "Good" ? COLORS.tealSoft :
                      lciBand === "Fair" ? COLORS.goldSoft : COLORS.redSoft
                  }
                ]}>
                  <Text style={[
                    styles.scoreBadgeText,
                    { color:
                        lciBand === "Excellent" ? COLORS.moss :
                        lciBand === "Good" ? COLORS.teal :
                        lciBand === "Fair" ? COLORS.gold : COLORS.red
                    }
                  ]}>{lciBand}</Text>
                </View>
                <Text style={styles.scoreScale}>Scale limits: 300 to 900</Text>
              </View>

              {/* LCI Score horizontal gauge */}
              <View style={styles.gaugeTrack}>
                <View style={[
                  styles.gaugeFill,
                  { 
                    width: `${((lciScore - 300) / 600) * 100}%`,
                    backgroundColor:
                      lciBand === "Excellent" ? COLORS.moss :
                      lciBand === "Good" ? COLORS.teal :
                      lciBand === "Fair" ? COLORS.gold : COLORS.red
                  }
                ]} />
              </View>
            </View>

            {/* Feature Attribution Trail (SHAP style) */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Score Feature Attribution Trail</Text>
              <Text style={styles.cardDesc}>
                Explainable AI values relative to a neutral baseline weaver score of 600.
              </Text>
              
              {weaverData?.lci?.contributions ? (
                weaverData.lci.contributions.map((contrib) => {
                  const isPos = contrib.contrib_score >= 0;
                  const absVal = Math.abs(contrib.contrib_score);
                  // Scale width percentage: cap max offset at 150 points for visual bar width
                  const barWidth = `${Math.min(50, (absVal / 150) * 50)}%`;
                  
                  return (
                    <View key={contrib.key} style={styles.shapRow}>
                      <Text style={styles.shapLabel}>{contrib.label}</Text>
                      <View style={styles.shapTrack}>
                        <View style={styles.shapCenterLine} />
                        <View style={[
                          styles.shapBar,
                          isPos ? styles.shapPosBar : styles.shapNegBar,
                          {
                            width: barWidth,
                            left: isPos ? "50%" : undefined,
                            right: !isPos ? "50%" : undefined
                          }
                        ]} />
                      </View>
                      <Text style={[styles.shapVal, isPos ? {color: COLORS.moss} : {color: COLORS.red}]}>
                        {isPos ? "+" : ""}{Math.round(contrib.contrib_score)}
                      </Text>
                    </View>
                  );
                })
              ) : (
                <Text style={styles.emptyLedger}>No score attribution trail available.</Text>
              )}
            </View>

            {/* Production Consistency Details */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Production Log Footprint</Text>
              <Text style={styles.cardDesc}>
                12-Month logs showing seasonal dips. Monsoon-adjusted CV filters out climatic volatility to prevent credit penalization.
              </Text>
              
              {weaverData?.lci?.cv && (
                <View style={styles.cvContainer}>
                  <View style={styles.cvItem}>
                    <Text style={styles.cvLabel}>Raw Volatility (CV)</Text>
                    <Text style={styles.cvValue}>{weaverData.lci.cv.raw}</Text>
                  </View>
                  <View style={styles.cvItem}>
                    <Text style={styles.cvLabel}>Monsoon-Adjusted</Text>
                    <Text style={styles.cvValue}>{weaverData.lci.cv.adjusted}</Text>
                  </View>
                  <View style={styles.cvItem}>
                    <Text style={styles.cvLabel}>Dip Explained?</Text>
                    <Text style={[styles.cvValue, {color: weaverData.lci.cv.explained ? COLORS.moss : COLORS.inkSoft}]}>
                      {weaverData.lci.cv.explained ? "Yes (Jul-Sep)" : "No"}
                    </Text>
                  </View>
                </View>
              )}
              
              <Text style={styles.voiceNudgeBox}>
                💡 *Credit Nudge:* {weaverData?.lci?.voice_nudge}
              </Text>
            </View>
          </View>
        )}

        {/* 4. ESCROW SIMULATOR TAB */}
        {activeTab === "escrow" && (
          <View style={styles.viewContent}>
            <Text style={styles.viewEyebrow}>Module 3 · Escrow Splits</Text>
            <Text style={styles.viewTitle}>Payment Escrow Simulator</Text>
            <Text style={styles.viewSub}>
              Visually calculate the automated split payouts of cooperative buyer settlements before execution.
            </Text>

            <View style={styles.card}>
              <View style={styles.formField}>
                <Text style={styles.formLabel}>Incoming Cooperative Payment (₹)</Text>
                <TextInput
                  style={styles.formInput}
                  keyboardType="numeric"
                  value={saleAmount}
                  onChangeText={setSaleAmount}
                  placeholder="e.g. 10000"
                />
              </View>
              <View style={styles.formField}>
                <Text style={styles.formLabel}>Description</Text>
                <TextInput
                  style={styles.formInput}
                  value={saleDesc}
                  onChangeText={setSaleDesc}
                  placeholder="e.g. Varanasi Silk Saree SHG Order"
                />
              </View>

              {/* Live splits display */}
              <View style={styles.splitLiveBox}>
                <Text style={styles.splitBoxHeader}>PROPOSED PAYMENT ROUTING SPLIT</Text>
                
                {/* 1. Monsoon sweep (5%) */}
                <View style={styles.splitRow}>
                  <Text style={styles.splitLabel}>🐖 Monsoon Reserve Sweep (5%)</Text>
                  <Text style={[styles.splitVal, { color: COLORS.gold }]}>
                    -₹{(parseFloat(saleAmount || 0) * 0.05).toFixed(2)}
                  </Text>
                </View>

                {/* 2. Loan repayment (15%) */}
                {activeLoan ? (
                  <View style={styles.splitRow}>
                    <Text style={styles.splitLabel}>🧶 NBFC Loan Repayment (15%)</Text>
                    <Text style={[styles.splitVal, { color: COLORS.red }]}>
                      -₹{Math.min(parseFloat(saleAmount || 0) * 0.15, activeLoan.outstanding_balance).toFixed(2)}
                    </Text>
                  </View>
                ) : (
                  <View style={[styles.splitRow, { opacity: 0.4 }]}>
                    <Text style={styles.splitLabel}>🧶 NBFC Loan Repayment (0% - No Active Loan)</Text>
                    <Text style={styles.splitVal}>-₹0.00</Text>
                  </View>
                )}

                {/* 3. Weaver release */}
                <View style={[styles.splitRow, styles.splitRowTotal]}>
                  <Text style={styles.splitLabelBold}>💼 Net Released to Wallet</Text>
                  <Text style={[styles.splitValBold, { color: COLORS.moss }]}>
                    ₹{(
                      parseFloat(saleAmount || 0) -
                      (parseFloat(saleAmount || 0) * 0.05) -
                      (activeLoan ? Math.min(parseFloat(saleAmount || 0) * 0.15, activeLoan.outstanding_balance) : 0)
                    ).toFixed(2)}
                  </Text>
                </View>
              </View>

              <TouchableOpacity 
                style={[styles.btn, { backgroundColor: COLORS.teal }]} 
                onPress={() => handleSimulateSale(null, null)}
              >
                <Text style={styles.btnText}>Execute Settlement Payout</Text>
              </TouchableOpacity>
            </View>

            {/* Loom Suraksha Micro-insurance simulator */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Loom Suraksha Micro-Insurance</Text>
              <Text style={styles.cardDesc}>
                Parametric insurance protection against loom breakdowns or medical emergencies.
              </Text>
              
              <View style={styles.insuranceToggleRow}>
                <View>
                  <Text style={styles.insuranceToggleTitle}>Loom Breakdown & Health Interruption</Text>
                  <Text style={styles.insuranceToggleSubtitle}>₹10/month  ·  ₹2,000 flat instant payout</Text>
                </View>
                <TouchableOpacity 
                  style={[
                    styles.toggleSwitch, 
                    enrolledSuraksha ? styles.toggleSwitchOn : styles.toggleSwitchOff
                  ]} 
                  onPress={() => handleToggleInsurance(!enrolledSuraksha)}
                >
                  <View style={[
                    styles.toggleKnob,
                    enrolledSuraksha ? styles.toggleKnobOn : styles.toggleKnobOff
                  ]} />
                </TouchableOpacity>
              </View>

              {enrolledSuraksha && (
                <View style={styles.insuranceActions}>
                  <TouchableOpacity style={[styles.btn, styles.btnOutline]} onPress={handleSimulateMonth}>
                    <Text style={styles.btnOutlineText}>Simulate 1 Month (Deduct ₹10)</Text>
                  </TouchableOpacity>
                  
                  <Text style={styles.insuranceClaimHeader}>File Simulated Claim Emergency:</Text>
                  <View style={styles.claimControls}>
                    <TouchableOpacity 
                      style={[styles.btn, { backgroundColor: COLORS.red, flex: 1, marginRight: 5 }]}
                      onPress={() => handleFileClaim("loom")}
                    >
                      <Text style={styles.btnText}>Loom Breakdown</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={[styles.btn, { backgroundColor: COLORS.red, flex: 1, marginLeft: 5 }]}
                      onPress={() => handleFileClaim("health")}
                    >
                      <Text style={styles.btnText}>Medical Interruption</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          </View>
        )}

        {/* 5. TELEGRAM HANDOFF TAB */}
        {activeTab === "assistant" && (
          <View style={styles.viewContent}>
            <Text style={styles.viewEyebrow}>Module 4 · Voice-First UI</Text>
            <Text style={styles.viewTitle}>Karigar Sahayak Bot</Text>
            <Text style={styles.viewSub}>
              Handoff neobank transactions directly to our WhatsApp/Telegram conversational assistant.
            </Text>

            <View style={styles.card}>
              <View style={styles.botIconBadge}>
                <Text style={styles.botIconText}>🤖</Text>
              </View>
              <Text style={styles.botName}>Voice Assistant "Karigar Sahayak"</Text>
              <Text style={styles.botDesc}>
                Handloom weavers can chat or send voice notes in their regional dialects to check balances, borrow yarn, or simulate sales. Our backend processes the voice inputs, executes underwriting math in real-time, and updates the shared database.
              </Text>
              
              {/* Audio Waveform mock card */}
              <View style={styles.audioWaveformCard}>
                <Text style={styles.audioWaveTitle}>Tamil Voice Note Transcription:</Text>
                <Text style={styles.audioWaveText}>
                  "பட்டு நூல் வாங்க 3000 ரூபாய் தேவைப்படுகிறது"{"\n"}
                  (Transcribed: "I need ₹3,000 to buy silk yarn.")
                </Text>
                <View style={styles.audioWaveformVisual}>
                  {[12, 18, 15, 25, 8, 30, 22, 16, 28, 10, 35, 14, 20, 8, 25, 15, 10, 5].map((h, i) => (
                    <View key={i} style={[styles.waveformBar, { height: h }]} />
                  ))}
                </View>
                <Text style={styles.audioWaveBot}>
                  🤖 Sahayak response: "Loom Loan of ₹3,000 approved and sent to Varanasi Weaving Mills."
                </Text>
              </View>

              <TouchableOpacity 
                style={[styles.btn, { backgroundColor: COLORS.teal }]} 
                onPress={() => Linking.openURL("https://t.me/KarigarPaybot")}
              >
                <Text style={styles.btnText}>Open Karigar Sahayak on Telegram</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Reset Database Trigger */}
        <TouchableOpacity style={styles.resetPrototypeBtn} onPress={handleResetDB}>
          <Text style={styles.resetPrototypeBtnText}>↺ Reset Database to Starting State</Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Premium Tab Navigation Bar */}
      <View style={styles.tabBar}>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === "wallet" && styles.tabItemActive]} 
          onPress={() => setActiveTab("wallet")}
        >
          <Text style={[styles.tabIcon, activeTab === "wallet" && styles.tabTextActive]}>💼</Text>
          <Text style={[styles.tabLabel, activeTab === "wallet" && styles.tabTextActive]}>Wallet</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tabItem, activeTab === "loan" && styles.tabItemActive]} 
          onPress={() => setActiveTab("loan")}
        >
          <Text style={[styles.tabIcon, activeTab === "loan" && styles.tabTextActive]}>🧶</Text>
          <Text style={[styles.tabLabel, activeTab === "loan" && styles.tabTextActive]}>Loom Loan</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tabItem, activeTab === "lci" && styles.tabItemActive]} 
          onPress={() => setActiveTab("lci")}
        >
          <Text style={[styles.tabIcon, activeTab === "lci" && styles.tabTextActive]}>📈</Text>
          <Text style={[styles.tabLabel, activeTab === "lci" && styles.tabTextActive]}>LCI Engine</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tabItem, activeTab === "escrow" && styles.tabItemActive]} 
          onPress={() => setActiveTab("escrow")}
        >
          <Text style={[styles.tabIcon, activeTab === "escrow" && styles.tabTextActive]}>💸</Text>
          <Text style={[styles.tabLabel, activeTab === "escrow" && styles.tabTextActive]}>Escrow</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tabItem, activeTab === "assistant" && styles.tabItemActive]} 
          onPress={() => setActiveTab("assistant")}
        >
          <Text style={[styles.tabIcon, activeTab === "assistant" && styles.tabTextActive]}>🤖</Text>
          <Text style={[styles.tabLabel, activeTab === "assistant" && styles.tabTextActive]}>Sahayak</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeContainer: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: "#FFFFFF"
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  brandMark: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: COLORS.ink,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 10,
  },
  brandMarkText: {
    fontSize: 16,
  },
  brandName: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.ink,
  },
  brandTag: {
    fontSize: 10,
    fontWeight: "600",
    color: COLORS.muted,
    textTransform: "uppercase",
    letterSpacing: 1.2,
  },
  refreshBtn: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: COLORS.inkSoft,
    backgroundColor: "transparent",
  },
  refreshBtnText: {
    fontSize: 12,
    fontWeight: "700",
    color: COLORS.inkSoft,
  },
  statusStripContainer: {
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingVertical: 6,
  },
  statusStrip: {
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
  },
  statusChip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 10,
    paddingVertical: 6,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusChipText: {
    fontSize: 12,
    color: COLORS.inkSoft,
  },
  statusBold: {
    fontWeight: "700",
    color: COLORS.ink,
  },
  chipDimmed: {
    opacity: 0.5,
  },
  splitFeedbackBanner: {
    backgroundColor: COLORS.mossSoft,
    borderColor: COLORS.moss,
    borderWidth: 1,
    borderRadius: 12,
    margin: 16,
    padding: 14,
  },
  splitFeedbackTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.moss,
    marginBottom: 2,
  },
  splitFeedbackText: {
    fontSize: 12,
    color: COLORS.inkSoft,
    lineHeight: 16,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  viewContent: {
    width: "100%",
  },
  viewEyebrow: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.red,
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 4,
  },
  viewTitle: {
    fontSize: 26,
    fontWeight: "700",
    color: COLORS.ink,
    marginBottom: 6,
  },
  viewSub: {
    fontSize: 14,
    color: COLORS.muted,
    lineHeight: 20,
    marginBottom: 20,
  },
  walletHero: {
    backgroundColor: COLORS.ink,
    borderRadius: 18,
    padding: 22,
    marginBottom: 16,
    shadowColor: COLORS.ink,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 4,
  },
  walletHeroTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 20,
  },
  walletLabel: {
    fontSize: 9,
    fontWeight: "700",
    color: "#FFFFFF",
    opacity: 0.7,
    letterSpacing: 1.2,
    marginBottom: 4,
  },
  walletBalance: {
    fontSize: 34,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  walletChipContainer: {
    alignItems: "flex-end",
  },
  walletCardChip: {
    width: 32,
    height: 24,
    borderRadius: 4,
    backgroundColor: "#C08A2C",
    marginTop: 6,
  },
  walletAccount: {
    fontSize: 11,
    color: "#FFFFFF",
    opacity: 0.8,
    letterSpacing: 1,
  },
  savingsVaultCard: {
    backgroundColor: "#FFFFFF",
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: 18,
    padding: 20,
    marginBottom: 16,
    shadowColor: COLORS.ink,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 1,
  },
  savingsVaultHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  savingsVaultIcon: {
    fontSize: 24,
    marginRight: 10,
  },
  savingsVaultTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: COLORS.ink,
  },
  savingsVaultSubtitle: {
    fontSize: 11,
    color: COLORS.muted,
  },
  savingsVaultBalance: {
    fontSize: 28,
    fontWeight: "700",
    color: COLORS.gold,
    marginBottom: 8,
  },
  savingsVaultHint: {
    fontSize: 11,
    color: COLORS.muted,
    lineHeight: 15,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: 18,
    padding: 20,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: COLORS.ink,
    marginBottom: 6,
  },
  cardDesc: {
    fontSize: 12,
    color: COLORS.muted,
    lineHeight: 17,
    marginBottom: 14,
  },
  simControls: {
    flexDirection: "column",
  },
  btn: {
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  btnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  btnOutline: {
    borderWidth: 1.5,
    borderColor: COLORS.borderStrong,
    backgroundColor: "transparent",
  },
  btnOutlineText: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.ink,
  },
  emptyLedger: {
    fontSize: 12,
    color: COLORS.muted,
    textAlign: "center",
    paddingVertical: 20,
  },
  ledgerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  ledgerInfo: {
    flex: 1,
    marginRight: 10,
  },
  ledgerDesc: {
    fontSize: 13,
    fontWeight: "600",
    color: COLORS.ink,
    marginBottom: 2,
  },
  ledgerTime: {
    fontSize: 11,
    color: COLORS.muted,
  },
  ledgerAmount: {
    fontSize: 13,
    fontWeight: "700",
  },
  ledgerCredit: {
    color: COLORS.moss,
  },
  ledgerDebit: {
    color: COLORS.red,
  },
  ledgerNeutral: {
    color: COLORS.inkSoft,
  },
  
  // Loom Loan Page Elements
  limitTrack: {
    height: 10,
    backgroundColor: "rgba(33, 26, 46, 0.08)",
    borderRadius: 5,
    marginTop: 10,
    overflow: "hidden",
  },
  limitFill: {
    height: "100%",
    backgroundColor: COLORS.teal,
    borderRadius: 5,
  },
  limitLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 6,
    marginBottom: 16,
  },
  limitLabelMin: {
    fontSize: 11,
    color: COLORS.muted,
  },
  limitLabelMax: {
    fontSize: 11,
    color: COLORS.muted,
  },
  limitDetails: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  limitDetailsText: {
    fontSize: 13,
    color: COLORS.muted,
  },
  limitDetailsVal: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.ink,
  },
  formField: {
    marginBottom: 16,
  },
  formLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.inkSoft,
    marginBottom: 6,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  formInput: {
    borderWidth: 1.5,
    borderColor: COLORS.borderStrong,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    fontSize: 14,
    color: COLORS.ink,
    backgroundColor: "#FFFFFF",
  },
  formHint: {
    fontSize: 11,
    color: COLORS.muted,
    marginTop: 5,
    lineHeight: 14,
  },
  shuttleLoader: {
    backgroundColor: COLORS.bg,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 10,
    marginTop: 16,
  },
  shuttleLoaderText: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.inkSoft,
    textAlign: "center",
    marginBottom: 6,
  },
  shuttleTrack: {
    height: 14,
    backgroundColor: "rgba(33, 26, 46, 0.05)",
    borderRadius: 7,
    overflow: "hidden",
    position: "relative",
  },
  shuttleThread: {
    position: "absolute",
    top: 6,
    left: 0,
    height: 2,
    backgroundColor: COLORS.red,
  },
  shuttleBlock: {
    position: "absolute",
    top: 2,
    width: 14,
    height: 10,
    borderRadius: 2,
    backgroundColor: COLORS.red,
  },
  loanStatusCard: {
    backgroundColor: COLORS.tealSoft,
    borderRadius: 10,
    padding: 16,
  },
  loanStatusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 4,
  },
  loanStatusLabel: {
    fontSize: 13,
    color: COLORS.inkSoft,
  },
  loanStatusVal: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.ink,
  },
  
  // LCI Engine Page Elements
  scoreDialCenter: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 10,
  },
  scoreNumber: {
    fontSize: 54,
    fontWeight: "700",
    color: COLORS.ink,
  },
  scoreBadge: {
    borderRadius: 999,
    paddingVertical: 4,
    paddingHorizontal: 12,
    marginTop: 6,
    marginBottom: 8,
  },
  scoreBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  scoreScale: {
    fontSize: 11,
    color: COLORS.muted,
  },
  gaugeTrack: {
    height: 6,
    backgroundColor: "rgba(33, 26, 46, 0.08)",
    borderRadius: 3,
    marginVertical: 10,
    overflow: "hidden",
  },
  gaugeFill: {
    height: "100%",
    borderRadius: 3,
  },
  shapRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginVertical: 6,
  },
  shapLabel: {
    width: 120,
    fontSize: 11,
    fontWeight: "600",
    color: COLORS.inkSoft,
  },
  shapTrack: {
    flex: 1,
    height: 8,
    backgroundColor: "rgba(33, 26, 46, 0.05)",
    borderRadius: 4,
    marginHorizontal: 10,
    position: "relative",
  },
  shapCenterLine: {
    position: "absolute",
    left: "50%",
    top: -2,
    bottom: -2,
    width: 1,
    backgroundColor: COLORS.borderStrong,
    zIndex: 1,
  },
  shapBar: {
    position: "absolute",
    height: "100%",
    borderRadius: 4,
  },
  shapPosBar: {
    backgroundColor: COLORS.moss,
  },
  shapNegBar: {
    backgroundColor: COLORS.red,
  },
  shapVal: {
    width: 32,
    textAlign: "right",
    fontSize: 11,
    fontWeight: "700",
  },
  cvContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    backgroundColor: COLORS.bg,
    borderRadius: 10,
    padding: 12,
    marginVertical: 10,
  },
  cvItem: {
    alignItems: "center",
  },
  cvLabel: {
    fontSize: 10,
    color: COLORS.muted,
    marginBottom: 4,
  },
  cvValue: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.ink,
  },
  voiceNudgeBox: {
    fontSize: 12,
    color: COLORS.inkSoft,
    backgroundColor: COLORS.goldSoft,
    borderRadius: 8,
    padding: 10,
    marginTop: 8,
    lineHeight: 16,
  },

  // Escrow Split & Savings Sweep
  splitLiveBox: {
    backgroundColor: COLORS.bg,
    borderRadius: 12,
    padding: 16,
    marginVertical: 14,
  },
  splitBoxHeader: {
    fontSize: 10,
    fontWeight: "700",
    color: COLORS.muted,
    letterSpacing: 1,
    marginBottom: 10,
  },
  splitRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderBottomWidth: 0.5,
    borderBottomColor: COLORS.border,
  },
  splitRowTotal: {
    borderBottomWidth: 0,
    paddingTop: 10,
    marginTop: 4,
  },
  splitLabel: {
    fontSize: 12,
    color: COLORS.inkSoft,
  },
  splitVal: {
    fontSize: 12,
    fontWeight: "700",
  },
  splitLabelBold: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.ink,
  },
  splitValBold: {
    fontSize: 14,
    fontWeight: "700",
  },
  insuranceToggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: COLORS.bg,
    borderRadius: 12,
    padding: 16,
  },
  insuranceToggleTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: COLORS.ink,
  },
  insuranceToggleSubtitle: {
    fontSize: 11,
    color: COLORS.muted,
    marginTop: 2,
  },
  toggleSwitch: {
    width: 44,
    height: 24,
    borderRadius: 12,
    padding: 2,
    justifyContent: "center",
  },
  toggleSwitchOn: {
    backgroundColor: COLORS.moss,
  },
  toggleSwitchOff: {
    backgroundColor: COLORS.muted,
  },
  toggleKnob: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 1,
  },
  toggleKnobOn: {
    alignSelf: "flex-end",
  },
  toggleKnobOff: {
    alignSelf: "flex-start",
  },
  insuranceActions: {
    marginTop: 16,
  },
  insuranceClaimHeader: {
    fontSize: 12,
    fontWeight: "700",
    color: COLORS.inkSoft,
    marginTop: 16,
    marginBottom: 8,
  },
  claimControls: {
    flexDirection: "row",
    justifyContent: "space-between",
  },

  // Telegram Assistant
  botIconBadge: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.tealSoft,
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "center",
    marginVertical: 14,
  },
  botIconText: {
    fontSize: 32,
  },
  botName: {
    fontSize: 16,
    fontWeight: "700",
    color: COLORS.ink,
    textAlign: "center",
    marginBottom: 6,
  },
  botDesc: {
    fontSize: 12,
    color: COLORS.inkSoft,
    lineHeight: 18,
    textAlign: "center",
    marginBottom: 16,
  },
  audioWaveformCard: {
    backgroundColor: COLORS.bg,
    borderColor: COLORS.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  audioWaveTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.muted,
    marginBottom: 4,
  },
  audioWaveText: {
    fontSize: 12,
    fontWeight: "600",
    color: COLORS.inkSoft,
    fontStyle: "italic",
    lineHeight: 16,
  },
  audioWaveformVisual: {
    flexDirection: "row",
    alignItems: "center",
    height: 40,
    marginVertical: 12,
  },
  waveformBar: {
    width: 3,
    backgroundColor: COLORS.teal,
    borderRadius: 1.5,
    marginHorizontal: 2,
    opacity: 0.7,
  },
  audioWaveBot: {
    fontSize: 11.5,
    color: COLORS.inkSoft,
    fontWeight: "600",
    borderTopWidth: 0.5,
    borderTopColor: COLORS.border,
    paddingTop: 8,
    marginTop: 4,
  },

  // Reset database triggers
  resetPrototypeBtn: {
    alignSelf: "center",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.muted,
    backgroundColor: "transparent",
    marginTop: 20,
    marginBottom: 40,
  },
  resetPrototypeBtnText: {
    fontSize: 11,
    fontWeight: "700",
    color: COLORS.muted,
  },
  globalLoader: {
    marginVertical: 10,
  },

  // Navigation Tabbar
  tabBar: {
    flexDirection: "row",
    height: 60,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: "#FFFFFF",
    paddingBottom: 4,
  },
  tabItem: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  tabItemActive: {
    backgroundColor: "rgba(14, 92, 91, 0.05)",
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: COLORS.muted,
  },
  tabTextActive: {
    color: COLORS.teal,
    fontWeight: "700",
  },

  // Error boundary page
  errorContainer: {
    flex: 1,
    backgroundColor: COLORS.bg,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  errorCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
    width: "100%",
    shadowColor: COLORS.ink,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 3,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: COLORS.red,
    marginBottom: 12,
    textAlign: "center",
  },
  errorText: {
    fontSize: 13,
    color: COLORS.ink,
    lineHeight: 18,
    marginBottom: 16,
    fontWeight: "600",
    textAlign: "center",
  },
  errorHint: {
    fontSize: 11.5,
    color: COLORS.muted,
    lineHeight: 16,
    backgroundColor: COLORS.bg,
    padding: 12,
    borderRadius: 10,
    marginBottom: 20,
  },
  errorBtn: {
    backgroundColor: COLORS.ink,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  errorBtnText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  }
});
