## Introduction
In general, tools are considered good if they do what they are supposed to do. If this is not the case,
this could lead to very expensive problems. One of the industries where this is the case is the semiconductor industry.

Unlike software, where an error may be corrected by issuing a patch, an error in an ASIC is irreversible and requires complete re-manufacturing.

Since respinning a design may cost millions of dollars, errors in silicon should be avoided.

Errors in silicon may be introduced in multiple ways, but this article will only consider errors that are introduced through errors that exist in tooling.

## Tool errors in ASIC Design
ASIC engineering is a complex process that involves multiple steps. In each step, part of the design process is completed and handed off to the next. Along the way, the result is tested for errors. Issues are fixed, leading ultimately to a (hopefully) working product.

However if a _tool_ contains an error, the consequences cascade. If an HDL parser contains an error that corrupts the translation from HDL to intermediate language, the corruption propagates through every subsequent step. More generally, any tool error in the flow compromises all downstream results.


As such, the quality of the end product depends heavily on the quality of the tools used in its production.

## SystemVerilog and Open-Source Tooling
One of the steps in the production process is HDL design. This step involves describing the circuit in a Hardware Description Language (HDL). SystemVerilog is one such HDL.

SystemVerilog was originally standardized in IEEE1800-2005 and was merged with base Verilog in IEEE1800-2009. It has since then been updated in 2012, 2017 and most recently in 2023.

Not only is SystemVerilog useful for synthesis of designs, but also for verification thereof using the language component SystemVerilog Assertions (SVA).

The IEEE1800 standard is open, and a collection of open-source tools have emerged that parse the language to provide several functions. To highlight a few; [Verilator](https://www.veripool.org/verilator/) parses the language to transform a design into C++ code, so that it may be compiled and run on a general purpose computer. [Slang](https://sv-lang.com/) offers functionality that parses the language into an abstract syntax tree (AST). [yosys-slang](https://github.com/povik/yosys-slang) uses slang to transform the AST into RTLIL so it can be used by [yosys](https://github.com/YosysHQ/yosys/) to synthesise a design.

## Current testing landscape
As concluded before, a tool needs to be reliable. Tool developers address this by equipping their tools with test cases. Furthermore, the [sv-tests](https://github.com/chipsalliance/sv-tests) project by the Chips Alliance intends to find all supported and missing SystemVerilog features in various Verilog tools.

They have published a [dashboard](https://chipsalliance.github.io/sv-tests-results/) in which the current state of support for different Verilog/SystemVerilog features is shown.

## Problems with existing Test Coverage
Though great work has been done by everyone involved to raise the quality of the tools, a number of problems exist:

1) The sv-tests project tries to achieve their goal by integrating tests from contributors. The test-framework has been established, now it's up to the community to fill in the gaps. This occurs on an ad-hoc, decentralized basis. The author is unaware if any concentrated effort taking place to fill in the gaps in the test-suite. 

The test-suite of the tools themselves and that of sv-tests do not necessarily line up. slang claims to fully support the IEEE1800-2023 standard, however sv-tests does not cover this standard. Without having reviewed the test suite of the tools itself, one can only assume slang's claim is true. A generic set of tests that can be applied to all tools that implement IEEE1800 standards is therefore very valuable.


2) The sv-tests suite of tests contains gaps. A cursory review of the implemented tests showed that for SVA, the test suites do not fully cover all features. Some features have no tests at all, such as Checkers. Note that this is but a sample, and may not generalize to the coverage of the rest of the language.

3) The dashboard of the sv-tests suite shows false positives. Some tools appear to pass tests, but upon closer inspection they do not.
In these particular casex, the worst scenario is likely a disappointed user that selected the tool based on the information the dashboard provided.

As we will see, false positives can have more serious consequences.

## A Concrete Example: False Positives in Practice
In this particular issue of yosys-slang, https://github.com/povik/yosys-slang/issues/77, a problem is described where intended use of the tool resulted in a false positive.
A testcase was written that should have resulted in a failure, but instead resulted in a pass. The AST was converted to invalid RTLIL that failed to trigger an error and as a result, the test passed.

According to the IEEE1800 standard, a `simple_immediate_assert_statement` embedded in an `initial_construct` was parsed erroneously.

The tool supports tests for assert in an `assert_comb` block, which is a `simple_immediate_assert_statement` in an `always_construct`.

False positives at this level are more dangerous. The assert statement is explicitly designed to test designs. A passing assert that should have failed leads
to a corruption propagating through subsequent steps.

In this case, the first line of defense has failed. Unsupported language did not result in an error when used.

The second line of defense has also failed. The sv-tests dashboard shows that for yosys-slang, the (16.2) assert test passes, but that is only half of the story. Even if the condition were false, the test would still pass.

There should be a test that also verifies the negative. Ie, if a true statement cause the test to pass, a false statement should cause the test to fail.


## The context problem
However, there is another problem. As the yosys-slang issue revealed, language features do not occur in isolation. Merely testing whether an assert statement is parsed correctly is not enough. In this example, an `assert` statement in an `initial` block behaves differently from an assert statement in an `always_comb` block.

A project like sv-tests, apart from its stated mission, should therefore also consider how the language features are tested in context.
Failure to do so will lead to false positives, as demonstrated above.

Summarizing, the following problems exist:
1) The test coverage contains gaps
2) Filling in these gaps depends on the community, which is slow and arbitrary.
3) The tool's own test suites do not always catch all problems, which could lead to false positives when used.
4) The overarching test framework sv-tests also contains false positives.
5) Language features need to be tested in context.


## Proposed approach
In order to address these problems, a different way of generating test cases is required. 
Due to previous experience with fuzzing techniques to find bugs in software, the author will explore applying these techniques to test case generation. 
Applying these techniques would mean that a graph that describes the language is assembled. 
All possible permutations will be contained in this graph. 
Corrected for recursion and infinity, this hopefully yields a set of paths through the graphs that can be followed to generated valid test cases. 
Positive paths describe valid paths through the graph, and should pass.
Negative paths describe invalid paths through the graph and should fail.
This should take care of the gaps problem, the testing-in-context problem as well as the false positives problem.

Progress may be followed her https://dehekkendekrekker.nl/tags/ieee1800-2023-tests/)

