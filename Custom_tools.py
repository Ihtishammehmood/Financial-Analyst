import yfinance as yf 
import logging
def get_profit_and_loss(symbol: str) -> str:
    """
    Use this function to get the income statement or profit and loss statement of a given stock symbol.

    Args:
        symbol (str): Stock ticker symbol.

    Returns:
        str: Financial statements as a markdown table.
    """
    try:
        ticker = yf.Ticker(symbol)
        financials = ticker.financials
        if financials.empty:
            return f"No financials data found for {symbol}"
        
        # Convert DataFrame to markdown
        markdown_table = financials.to_markdown()
        return markdown_table
    except Exception as e:
        logging.error(f"Error retrieving financials for {symbol}: {e}")
        return f"Error: {str(e)}"
    
  
def balance_sheet(symbol: str) -> str:
    """
    Use this function to get balance sheet of a given stock symbol.

    Args:
        symbol (str): Stock ticker symbol.

    Returns:
        str: balance_sheet as a markdown table.
    """
    try:
        ticker = yf.Ticker(symbol)
        balance_sheet = ticker.balance_sheet
        if balance_sheet.empty:
            return f"No balance_sheet data found for {symbol}"
        
        # Convert DataFrame to markdown
        markdown_table = balance_sheet.to_markdown()
        return markdown_table
    except Exception as e:
        logging.error(f"Error retrieving balance_sheet for {symbol}: {e}")
        return f"Error: {str(e)}"
    

def cash_flow(symbol: str) -> str:
    """
    Use this function to get the cash flow statement of a given stock symbol.

    Args:
        symbol (str): Stock ticker symbol.

    Returns:
        str: cash flow statement as a markdown table.
    """
    try:
        ticker = yf.Ticker(symbol)
        cash_flow = ticker.cash_flow
        if cash_flow.empty:
            return f"No cash_flow data found for {symbol}"
        
        # Convert DataFrame to markdown
        markdown_table = cash_flow.to_markdown()
        return markdown_table
    except Exception as e:
        logging.error(f"Error retrieving cash_flow for {symbol}: {e}")
        return f"Error: {str(e)}"
    
 